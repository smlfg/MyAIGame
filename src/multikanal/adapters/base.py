"""Abstract adapter interface for agent output capture."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Base class for agent adapters.

    Each adapter captures output from a specific CLI agent
    and sends it to the MultiKanalAgent daemon for narration.
    """

    def __init__(self, daemon_url: str = "http://127.0.0.1:7742"):
        self.daemon_url = daemon_url.rstrip("/")

    @abstractmethod
    def capture(self, **kwargs) -> str:
        """Capture agent output. Returns the raw text captured.

        Implementation varies per agent:
        - claude_hook: receives JSON on stdin from hook
        - codex_wrapper: runs codex CLI and reads JSONL
        - opencode_sse: subscribes to SSE stream
        """
        ...

    @staticmethod
    def _guess_language(text: str) -> str:
        """Tiny heuristic language guess (de/en/unknown)."""
        lower = text.lower()
        if any(ch in lower for ch in ("ä", "ö", "ü", "ß")) or any(
            kw in lower for kw in (" und ", " nicht ", " kann ", " warum ", " wie ")
        ):
            return "de"
        if any(kw in lower for kw in (" the ", " and ", " why ", " how ", " please ")):
            return "en"
        return ""

    def send_to_daemon(
        self,
        text: str,
        source: str = "unknown",
        language: str | None = None,
        timeout: float = 1.5,
    ) -> dict[str, Any] | None:
        """Send captured text to the daemon for narration.

        Returns the daemon response or None on failure.
        Never raises — follows the Iron Rule.
        """
        if not text.strip():
            return None

        lang = language or self._guess_language(text)

        try:
            import httpx

            resp = httpx.post(
                f"{self.daemon_url}/narrate",
                json={"text": text, "source": source, "language": lang},
                timeout=timeout,
            )
            return resp.json()
        except Exception:
            # Iron Rule: never let audio failures affect the agent
            return None
