"""Claude Code provider — subprocess wrapper around the claude CLI."""

from __future__ import annotations

import shutil
from typing import Any

from tui.providers.base import BaseProvider


class ClaudeCodeProvider(BaseProvider):
    """Provider that wraps the Claude Code CLI via subprocess.

    In the prototype, returns mock data. Real implementation would
    call `claude` CLI with --output-format json and parse results.
    """

    MOCK_RESPONSES = [
        "I've analyzed the codebase. The portable skill format looks clean — "
        "the SPEC.md defines a solid abstraction layer.",
        "Running the delegation hierarchy: chef-lite → chef → chef-async → delegate. "
        "Each layer adds context gathering.",
        "The `$ARGUMENTS` placeholder is the key innovation — it's universal across "
        "all three target runtimes without transformation.",
        "Skill discovered: cost-tier 'low' with delegate_code + shell dependencies. "
        "OpenCode MCP is the primary execution engine.",
        "Focus session active. Next milestone: implement the transpiler for all 30 skills "
        "to Claude Code / Codex / OpenCode targets.",
    ]

    def __init__(self):
        self._response_idx = 0
        self._cli_available = shutil.which("claude") is not None
        self._total_tokens = 0
        self._total_cost = 0.0

    @property
    def name(self) -> str:
        return "Claude Code"

    @property
    def provider_id(self) -> str:
        return "claude-code"

    def send_prompt(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Send prompt to Claude Code CLI (mock implementation)."""
        # Mock: cycle through canned responses
        response = self.MOCK_RESPONSES[self._response_idx % len(self.MOCK_RESPONSES)]
        self._response_idx += 1

        tokens = len(prompt.split()) * 2 + len(response.split())
        cost = tokens * 0.000015  # Opus ~$15/1M tokens

        self._total_tokens += tokens
        self._total_cost += cost

        return {
            "content": response,
            "tokens": tokens,
            "cost": cost,
            "model": "claude-opus-4-6",
            "provider": self.provider_id,
        }

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "skills": True,
            "async_sessions": True,
            "multi_agent": True,
            "voice": True,
            "file_ops": True,
            "web_search": True,
            "models": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"],
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "healthy": True,  # Mock: always healthy in prototype
            "model": "claude-opus-4-6",
            "latency_ms": 42,
            "error": None,
            "cli_available": self._cli_available,
        }
