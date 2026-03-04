"""Codex CLI provider stub."""

from __future__ import annotations

import shutil
from typing import Any

from tui.providers.base import BaseProvider


class CodexProvider(BaseProvider):
    """Provider wrapping OpenAI Codex CLI.

    Stub: returns mock responses. Real implementation would call
    `codex` CLI or the OpenAI Responses API directly.
    """

    MOCK_RESPONSES = [
        "Codex: Analyzing the portable skill directory structure. "
        "All 29 skills ported to .codex/skills/ format with full directory trees.",
        "Codex: The abstract tool syntax {{delegate_code(prompt, dir)}} maps cleanly "
        "to my native `codex_run(prompt, dir)` call.",
        "Codex: Skill transpilation complete. 30 skills → .codex/skills/ output. "
        "Scripts copied to scripts/ subdirectories.",
        "Codex: Running in agent mode. File edits applied, tests passing.",
    ]

    def __init__(self):
        self._response_idx = 0
        self._cli_available = shutil.which("codex") is not None

    @property
    def name(self) -> str:
        return "Codex CLI"

    @property
    def provider_id(self) -> str:
        return "codex"

    def send_prompt(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Send prompt to Codex CLI (mock implementation)."""
        response = self.MOCK_RESPONSES[self._response_idx % len(self.MOCK_RESPONSES)]
        self._response_idx += 1

        tokens = len(prompt.split()) * 2 + len(response.split())
        cost = tokens * 0.000003  # o4-mini ~$3/1M

        return {
            "content": response,
            "tokens": tokens,
            "cost": cost,
            "model": "o4-mini",
            "provider": self.provider_id,
        }

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "skills": True,
            "async_sessions": False,
            "multi_agent": False,
            "voice": False,
            "file_ops": True,
            "web_search": True,
            "models": ["o4-mini", "o3"],
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "healthy": self._cli_available,
            "model": "o4-mini",
            "latency_ms": -1 if not self._cli_available else 88,
            "error": None if self._cli_available else "codex CLI not found in PATH",
            "cli_available": self._cli_available,
        }
