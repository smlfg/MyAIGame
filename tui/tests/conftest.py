"""Shared pytest fixtures for the MyAIGame TUI test suite."""

from __future__ import annotations

import sqlite3
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from tui.providers.base import BaseProvider
from tui.state.database import _run_migrations


# ---------------------------------------------------------------------------
# tmp_skills_dir — temp directory with 3 sample SKILL.md files
# ---------------------------------------------------------------------------

SKILL_CHEF = textwrap.dedent("""\
    ---
    name: chef
    description: Delegate implementation tasks to OpenCode
    cost_tier: low
    category: execution
    delegate: opencode
    dependencies:
      - opencode
    tags:
      - delegation
      - code
    ---
    # Chef

    Delegate code generation to OpenCode MCP.

    ## Usage
    /chef $ARGUMENTS

    ## Template
    implement: $ARGUMENTS
""")

SKILL_RESEARCH = textwrap.dedent("""\
    ---
    name: research
    description: Web research via Gemini Flash
    cost_tier: low
    category: research
    delegate: gemini
    dependencies: []
    tags:
      - research
      - web
    ---
    # Research

    Run a quick web research query using Gemini.

    ## Usage
    /research $ARGUMENTS

    ## Template
    research: $ARGUMENTS
""")

SKILL_FOCUS = textwrap.dedent("""\
    ---
    name: focus
    description: Start a focused work session
    cost_tier: free
    category: productivity
    delegate: local
    dependencies: []
    tags:
      - focus
      - adhd
    ---
    # Focus

    Set a focus goal for the current session.

    ## Usage
    /focus $ARGUMENTS
""")


@pytest.fixture
def tmp_skills_dir(tmp_path: Path) -> Path:
    """Create a temp directory with 3 sample SKILL.md files."""
    for name, content in [
        ("chef", SKILL_CHEF),
        ("research", SKILL_RESEARCH),
        ("focus", SKILL_FOCUS),
    ]:
        skill_dir = tmp_path / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(content)
    return tmp_path


# ---------------------------------------------------------------------------
# mock_provider — MockProvider returning canned responses
# ---------------------------------------------------------------------------

class MockProvider(BaseProvider):
    """Test double for BaseProvider."""

    def __init__(self, provider_id: str = "mock", healthy: bool = True):
        self._provider_id = provider_id
        self._healthy = healthy
        self.calls: list[dict] = []

    @property
    def name(self) -> str:
        return f"Mock ({self._provider_id})"

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def send_prompt(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        result = {
            "content": f"mock response to: {prompt[:40]}",
            "tokens": 10,
            "cost": 0.0001,
            "model": "mock-model",
            "provider": self._provider_id,
        }
        self.calls.append({"prompt": prompt, "kwargs": kwargs, "result": result})
        return result

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "skills": True,
            "async_sessions": False,
            "multi_agent": False,
            "voice": False,
            "file_ops": True,
            "web_search": False,
            "models": ["mock-model"],
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "healthy": self._healthy,
            "model": "mock-model",
            "latency_ms": 1,
            "error": None if self._healthy else "mock unhealthy",
        }


@pytest.fixture
def mock_provider() -> MockProvider:
    """Return a fresh MockProvider instance."""
    return MockProvider()


# ---------------------------------------------------------------------------
# tmp_db — in-memory SQLite via state/database module
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(monkeypatch):
    """Patch database.py to use an in-memory SQLite connection for each test."""
    import tui.state.database as db_module

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    _run_migrations(conn)
    conn.commit()

    # Patch _get_connection to always return our in-memory connection
    monkeypatch.setattr(db_module, "_get_connection", lambda: conn)

    yield conn

    conn.close()


# ---------------------------------------------------------------------------
# sample_config — simple config dict with test defaults
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_config() -> dict:
    """Return a config dict with test-safe defaults."""
    return {
        "default_provider": "mock",
        "skills_dir": "/tmp/test-skills",
        "db_path": ":memory:",
        "log_level": "DEBUG",
        "cost_alert_threshold": 1.0,
        "focus_default_minutes": 25,
        "theme": "dark",
        "providers": {
            "claude-code": {"model": "claude-opus-4-6", "enabled": True},
            "opencode": {"model": "claude-sonnet-4-6", "enabled": True},
            "codex": {"model": "o4-mini", "enabled": False},
        },
    }
