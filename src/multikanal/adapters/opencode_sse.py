"""OpenCode SSE (Server-Sent Events) adapter with live and final modes.

Subscribes to OpenCode's event stream and provides:
- LIVE updates during work (message.created/updated → immediate narration)
- FINAL summary at session.idle (accumulates → narrates once)
"""

import asyncio
import json
import logging
from typing import Optional

import httpx

from .base import BaseAdapter

logger = logging.getLogger("multikanal.adapters.opencode_sse")


class OpenCodeSSEAdapter(BaseAdapter):
    """Subscribes to OpenCode SSE stream with live updates + final summary."""

    def __init__(
        self,
        daemon_url: str = "http://127.0.0.1:7742",
        sse_url: str = "http://localhost:3000/events",
    ):
        super().__init__(daemon_url)
        self._sse_url = sse_url
        self._accumulated: list[str] = []
        self._accumulation_lock = asyncio.Lock()
        self._shutdown = asyncio.Event()

    def capture(self, **kwargs) -> str:
        """Blocking capture - waits for session.idle and returns accumulated text."""
        import asyncio

        try:
            asyncio.run(self._subscribe_final())
        except KeyboardInterrupt:
            logger.info("SSE subscription interrupted by user")
        return "\n".join(self._accumulated)

    async def capture_async(self, **kwargs) -> str:
        """Async capture - for use in async contexts."""
        await self._subscribe_final()
        return "\n".join(self._accumulated)

    async def listen_live(self):
        """Listen for events and send LIVE updates immediately.

        This is a non-blocking call that:
        1. Sends live updates after each message.created/updated
        2. Accumulates text for final summary
        3. Sends final summary at session.idle
        """
        await self._subscribe_live()

    async def _subscribe_live(self):
        """Connect to SSE stream with LIVE updates + accumulation."""
        self._shutdown = asyncio.Event()

        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("GET", self._sse_url) as response:
                    event_type = ""
                    async for line in response.aiter_lines():
                        if self._shutdown.is_set():
                            logger.info("SSE shutdown requested")
                            break

                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                            continue

                        if line.startswith("data:"):
                            data = line[5:].strip()
                            if event_type:
                                await self._process_event_live(event_type, data)

            except httpx.ConnectError as e:
                logger.warning("SSE connection failed: %s", e)
            except Exception as e:
                logger.warning("SSE error: %s", e)

    async def _process_event_live(self, event_type: str, raw_data: str):
        """Process SSE event - LIVE update + accumulate."""
        text = self._extract_text(event_type, raw_data)
        if not text:
            return

        # LIVE: Send immediately (non-blocking)
        asyncio.create_task(self._send_live(text))

        # ACCUMULATE: For final summary
        async with self._accumulation_lock:
            self._accumulated.append(text)

        # FINAL: At session.idle, send accumulated text
        if event_type == "session.idle":
            await self._send_final()

    async def _send_live(self, text: str):
        """Send live update to daemon."""
        try:
            language = self._guess_language(text)
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: httpx.post(
                    f"{self.daemon_url}/narrate",
                    json={
                        "text": text,
                        "source": "opencode_live",
                        "language": language,
                    },
                    timeout=1.5,
                ),
            )
            if resp.status_code == 200:
                logger.debug("Live update sent: %d chars", len(text))
        except Exception as e:
            logger.debug("Failed to send live update: %s", e)

    async def _send_final(self):
        """Send final accumulated summary to daemon."""
        async with self._accumulation_lock:
            if not self._accumulated:
                return
            text = "\n".join(self._accumulated)
            self._accumulated = []

        try:
            language = self._guess_language(text)
            resp = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: httpx.post(
                    f"{self.daemon_url}/narrate",
                    json={
                        "text": text,
                        "source": "opencode_final",
                        "language": language,
                    },
                    timeout=30,
                ),
            )
            if resp.status_code == 200:
                logger.info("Final summary sent: %d chars", len(text))
        except Exception as e:
            logger.debug("Failed to send final summary: %s", e)

    async def _subscribe_final(self):
        """Blocking subscribe - waits for session.idle, returns accumulated text."""
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("GET", self._sse_url) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                            continue

                        if line.startswith("data:"):
                            data = line[5:].strip()
                            text = self._extract_text(event_type, data)
                            if text:
                                async with self._accumulation_lock:
                                    self._accumulated.append(text)

                            if event_type == "session.idle":
                                return  # Done accumulating

            except httpx.ConnectError as e:
                logger.warning("SSE connection failed: %s", e)
            except Exception as e:
                logger.warning("SSE error: %s", e)

    def _extract_text(self, event_type: str, raw_data: str) -> str:
        """Extract text from SSE event data."""
        if event_type == "session.idle":
            return ""  # No content, just signal

        try:
            data = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            return raw_data if event_type == "message.updated" else ""

        # message.created / message.updated events
        if event_type in ("message.created", "message.updated"):
            role = data.get("role", "")
            if role != "assistant":
                return ""

            content = data.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                return "\n".join(texts)

        return ""

    def listen_and_narrate(self) -> str:
        """Legacy method - blocks until session.idle, then narrates."""
        text = self.capture()
        if text:
            self.send_to_daemon(text, source="opencode")
        return text

    def stop(self):
        """Signal the listener to stop."""
        self._shutdown.set()
