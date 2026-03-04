"""
Event dataclasses for the unified TUI event system.

Every event carries at minimum: type, timestamp, session_id.
Specific events extend with domain-specific fields per TUI_EVENTS.md.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

@dataclass
class Event:
    type: str
    timestamp: float = field(default_factory=time.time)
    data: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Tool lifecycle
# ---------------------------------------------------------------------------

@dataclass
class PreToolUseEvent(Event):
    """Fires before the backend executes any tool.

    Handlers may return:
        {"allow": True}                       — proceed (default, same as None)
        {"block": True, "reason": "..."}      — prevent execution
        {"modify": True, "params": {...}}     — rewrite tool parameters
    """
    type: str = "pre_tool_use"
    tool: str = ""
    params: dict = field(default_factory=dict)
    session_id: str = ""
    cwd: str = ""


@dataclass
class PostToolUseEvent(Event):
    """Fires after the backend completes a tool call.

    Handlers may return:
        {"context": "..."}  — additional context injected into agent's next turn
        None                — side-effects only, no injection
    """
    type: str = "post_tool_use"
    tool: str = ""
    params: dict = field(default_factory=dict)
    result: str = ""        # truncated to 4000 chars by the TUI
    duration_ms: int = 0
    success: bool = True
    session_id: str = ""
    cwd: str = ""


@dataclass
class ErrorEvent(Event):
    """Fires when a tool call fails (hard crash or soft error pattern match)."""
    type: str = "on_error"
    tool: str = ""
    params: dict = field(default_factory=dict)
    error: str = ""
    error_type: str = "hard"   # "hard" | "soft"
    session_id: str = ""
    cwd: str = ""


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------

@dataclass
class SessionStartEvent(Event):
    type: str = "session_start"
    session_id: str = ""
    backend: str = ""    # "claude-code" | "codex" | "opencode"
    project_dir: str = ""


@dataclass
class SessionStopEvent(Event):
    type: str = "session_stop"
    session_id: str = ""
    backend: str = ""
    transcript_path: str | None = None
    error_count: int = 0
    duration_s: float = 0.0


# ---------------------------------------------------------------------------
# Agent lifecycle (sub-agents / background tasks)
# ---------------------------------------------------------------------------

@dataclass
class AgentEvent(Event):
    """Generic agent event — prefer the concrete subclasses below."""
    agent_name: str = ""
    agent_status: str = ""   # "spawned" | "completed" | "error"


@dataclass
class AgentSpawnEvent(Event):
    type: str = "agent_spawn"
    agent_id: str = ""
    parent_session_id: str = ""
    task: str = ""
    backend: str = ""
    async_: bool = False


@dataclass
class AgentCompleteEvent(Event):
    type: str = "agent_complete"
    agent_id: str = ""
    parent_session_id: str = ""
    success: bool = True
    result_summary: str = ""    # first 500 chars
    files_changed: list[str] = field(default_factory=list)
    duration_s: float = 0.0


# ---------------------------------------------------------------------------
# ADHS / focus timer
# ---------------------------------------------------------------------------

@dataclass
class FocusEvent(Event):
    """Simplified focus event (as required by team task spec)."""
    type: str = "focus_check"
    goal: str = ""
    minutes_elapsed: int = 0
    action: str = ""   # "check" | "remind" | "celebrate"


@dataclass
class FocusCheckEvent(Event):
    """Full focus-check event with all context fields (per TUI_EVENTS.md)."""
    type: str = "focus_check"
    session_id: str = ""
    focus_goal: str = ""
    elapsed_min: float = 0.0
    parked_ideas: list[str] = field(default_factory=list)
    checkpoint_count: int = 0


@dataclass
class ContextDegradationEvent(Event):
    """Fires when session exceeds token/time threshold."""
    type: str = "context_degradation"
    session_id: str = ""
    elapsed_min: float = 0.0
    estimated_context_pct: float = 0.0    # 0.0–1.0
    suggestion: str = "Consider /compact or /recap"


# ---------------------------------------------------------------------------
# User input
# ---------------------------------------------------------------------------

@dataclass
class SessionInputEvent(Event):
    """Fires when the user submits a prompt."""
    type: str = "session_input"
    session_id: str = ""
    text: str = ""
    is_skill: bool = False
    skill_name: str | None = None


# ---------------------------------------------------------------------------
# ToolUseEvent alias (for backward compat with team task spec)
# ---------------------------------------------------------------------------

@dataclass
class ToolUseEvent(Event):
    """Alias used in team task spec. Prefer PostToolUseEvent for new code."""
    type: str = "tool_use"
    tool_name: str = ""
    params: dict = field(default_factory=dict)
    result: Any = None   # filled in post_tool_use
