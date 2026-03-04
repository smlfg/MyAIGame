"""OpenCode provider — MCP client wrapper."""

from __future__ import annotations

from typing import Any

from tui.providers.base import BaseProvider


class OpenCodeProvider(BaseProvider):
    """Provider wrapping OpenCode via MCP client.

    Stub: returns mock responses. Real implementation would connect to
    the OpenCode MCP server and call opencode_ask / opencode_run tools.
    """

    MOCK_RESPONSES = [
        "OpenCode: Session created. Analyzing project context with gather-context.sh...",
        "OpenCode: Running async task. Session ID: ses_mock_001. "
        "Check progress with /chef-async status ses_mock_001.",
        "OpenCode: Task complete. Files modified: tui/app.py, tui/providers/opencode.py. "
        "Run git diff to review changes.",
        "OpenCode: Skill engine initialized. 30 skills discovered in portable/. "
        "Transpiler ready for all targets.",
        "OpenCode: Multi-agent session active. Planner → Executor → Analyzer pipeline running.",
    ]

    def __init__(self):
        self._response_idx = 0
        self._session_counter = 0

    @property
    def name(self) -> str:
        return "OpenCode"

    @property
    def provider_id(self) -> str:
        return "opencode"

    def send_prompt(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Send prompt via OpenCode MCP (mock implementation)."""
        response = self.MOCK_RESPONSES[self._response_idx % len(self.MOCK_RESPONSES)]
        self._response_idx += 1
        self._session_counter += 1

        tokens = len(prompt.split()) * 2 + len(response.split())
        cost = tokens * 0.000003  # Sonnet ~$3/1M

        return {
            "content": response,
            "tokens": tokens,
            "cost": cost,
            "model": "claude-sonnet-4-6",
            "provider": self.provider_id,
            "session_id": f"ses_mock_{self._session_counter:03d}",
        }

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "skills": True,
            "async_sessions": True,
            "multi_agent": True,
            "voice": False,
            "file_ops": True,
            "web_search": True,
            "models": ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5"],
        }

    def health_check(self) -> dict[str, Any]:
        # In production: ping the MCP server
        return {
            "healthy": True,
            "model": "claude-sonnet-4-6",
            "latency_ms": 15,
            "error": None,
            "mcp_connected": False,  # Not actually connected in prototype
        }
