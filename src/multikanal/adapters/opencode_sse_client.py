#!/usr/bin/env python3
"""
OpenCode SSE Client for MultiKanalAgent

Connects to OpenCode's /global/event SSE endpoint and listens for:
- message.updated
- session.created
- session.updated
etc.

Events are forwarded to the daemon via HTTP callback.
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [opencode_sse] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_OPENCODE_URL = "http://127.0.0.1:4096"
DEFAULT_DAEMON_URL = "http://127.0.0.1:7742"


@dataclass
class OpenCodeEvent:
    """Parsed OpenCode event."""

    type: str
    directory: str
    timestamp: datetime
    properties: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict) -> "OpenCodeEvent":
        return cls(
            type=payload.get("type", "unknown"),
            directory=payload.get("directory", ""),
            timestamp=datetime.now(),
            properties=payload.get("properties", {}),
        )


class OpenCodeSSEClient:
    """
    Connects to OpenCode's SSE endpoint and forwards events.

    Usage:
        client = OpenCodeSSEClient(
            opencode_url="http://127.0.0.1:4096",
            daemon_url="http://127.0.0.1:7742",
        )
        await client.connect()
    """

    def __init__(
        self,
        opencode_url: str = DEFAULT_OPENCODE_URL,
        daemon_url: str = DEFAULT_DAEMON_URL,
        on_event: Optional[Callable[[OpenCodeEvent], None]] = None,
    ):
        self.opencode_url = opencode_url.rstrip("/")
        self.daemon_url = daemon_url.rstrip("/")
        self.on_event = on_event
        self._running = False
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self, timeout: float = 30.0) -> None:
        """Connect to OpenCode SSE and start listening."""
        if self._running:
            logger.warning("Already connected!")
            return

        self._client = httpx.AsyncClient(timeout=timeout)
        self._running = True

        sse_url = f"{self.opencode_url}/global/event"
        logger.info(f"Connecting to OpenCode SSE: {sse_url}")

        try:
            async with self._client.stream("GET", sse_url) as response:
                if response.status_code != 200:
                    logger.error(f"SSE connection failed: {response.status_code}")
                    return

                logger.info("Connected to OpenCode SSE stream")

                async for line in response.aiter_lines():
                    if not self._running:
                        break

                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            payload = json.loads(data)
                            event = OpenCodeEvent.from_payload(payload)
                            await self._handle_event(event)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse event: {e}")
                            continue

        except httpx.ConnectError as e:
            logger.error(f"Connection error: {e}")
        except Exception as e:
            logger.error(f"SSE error: {e}")
        finally:
            self._running = False
            if self._client:
                await self._client.aclose()
                self._client = None

    async def _handle_event(self, event: OpenCodeEvent) -> None:
        """Process a received event."""
        logger.info(f"Event: {event.type} in {event.directory}")

        if self.on_event:
            self.on_event(event)

        if event.type.startswith("message."):
            await self._forward_to_daemon(event)

    async def _forward_to_daemon(self, event: OpenCodeEvent) -> None:
        """Forward message events to our daemon for narration."""
        if not event.properties:
            return

        message_data = event.properties.get("info", {})
        if not message_data:
            return

        content = message_data.get("content", "")
        role = message_data.get("role", "unknown")

        if not content:
            return

        narration_text = self._format_for_narration(event.type, role, content)
        if narration_text:
            await self._send_narration(narration_text)

    def _format_for_narration(self, event_type: str, role: str, content: str) -> str:
        """Format event for narration."""
        role_name = role.capitalize() if role else "Unbekannt"

        if event_type == "message.updated":
            return f"{role_name} hat eine Nachricht gesendet: {content[:200]}..."
        elif event_type == "message.created":
            return f"Neue Nachricht von {role_name}: {content[:200]}..."

        return f"{role_name}: {content[:200]}..."

    async def _send_narration(self, text: str) -> None:
        """Send text to daemon for narration."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.daemon_url}/narrate",
                    json={"text": text, "source": "opencode"},
                    timeout=10.0,
                )
                logger.debug(f"Sent narration: {text[:50]}...")
        except Exception as e:
            logger.error(f"Failed to send narration: {e}")

    async def stop(self) -> None:
        """Stop the SSE client."""
        self._running = False
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("OpenCode SSE client stopped")


async def main():
    """Run the OpenCode SSE client."""
    client = OpenCodeSSEClient()

    import signal

    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(client.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await client.connect()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())
