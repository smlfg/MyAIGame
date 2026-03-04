"""TTSClient — connects to the narration daemon at http://localhost:7742.

The narration daemon (port 7742) is a queue manager that wraps the
Edge TTS server (port 5050, OpenAI-compatible). The TUI always talks
to port 7742 for narration so the daemon handles priority queuing.

Fire-and-forget pattern: narrate() schedules an asyncio task and
returns immediately, never blocking the main TUI event loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

DAEMON_BASE_URL = "http://localhost:7742"


class TTSClient:
    """HTTP client for the narration daemon at port 7742.

    All public methods are fire-and-forget: they schedule asyncio tasks
    and return immediately. The caller never waits for audio playback.

    Example:
        client = TTSClient()
        client.narrate("Research complete.", priority="normal")  # non-blocking
        available = await client.is_available()
    """

    def __init__(self, base_url: str = DAEMON_BASE_URL) -> None:
        self._base_url = base_url.rstrip("/")
        self._voice: str = "florian"
        self._speed: float = 1.0
        self._session: aiohttp.ClientSession | None = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_voice(self, voice: str) -> None:
        """Set the TTS voice name (e.g. 'florian', 'katja')."""
        self._voice = voice

    def set_speed(self, speed: float) -> None:
        """Set playback speed (1.0 = normal, 0.5-2.0 range)."""
        self._speed = max(0.5, min(2.0, speed))

    # ------------------------------------------------------------------
    # Core public API
    # ------------------------------------------------------------------

    def narrate(self, text: str, priority: str = "normal") -> None:
        """Queue text for narration. Fire-and-forget, never blocks.

        Priority levels accepted by the daemon:
            "urgent"  — errors, critical events (highest)
            "normal"  — completions, agent messages
            "low"     — background narration, status updates

        If the daemon is not running, logs a warning and continues silently.
        """
        asyncio.create_task(self._post_narrate(text, priority))

    async def is_available(self) -> bool:
        """Return True if the narration daemon is reachable."""
        try:
            session = await self._get_session()
            async with session.get(f"{self._base_url}/health") as resp:
                return resp.status == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal async implementation
    # ------------------------------------------------------------------

    async def _post_narrate(self, text: str, priority: str) -> None:
        """POST /narrate to the daemon. Called via asyncio.create_task."""
        if not text or not text.strip():
            return

        payload: dict[str, Any] = {
            "text": text.strip(),
            "priority": priority,
            "voice": self._voice,
            "speed": self._speed,
        }

        try:
            session = await self._get_session()
            async with session.post(
                f"{self._base_url}/narrate", json=payload
            ) as resp:
                if resp.status not in (200, 201, 202):
                    body = await resp.text()
                    logger.warning(
                        "Narration daemon returned %d: %s", resp.status, body[:200]
                    )
        except aiohttp.ClientConnectorError:
            logger.warning(
                "Narration daemon not reachable at %s — skipping narration.",
                self._base_url,
            )
        except asyncio.TimeoutError:
            logger.warning("Narration daemon timed out — skipping.")
        except Exception as exc:
            logger.warning("TTS narrate failed unexpectedly: %s", exc)
