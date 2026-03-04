# Unified TUI Event System

> How the portable TUI handles hooks, plugins, and lifecycle events across
> Claude Code, Codex CLI, and OpenCode backends.

---

## 1. Design Principles

The unified TUI sits **between the user and the backend agent**. It intercepts the communication stream and emits events at well-defined points. Plugins subscribe to these events.

```
User Input
    |
    v
[TUI Event: session_input]
    |
    v
[TUI Event: pre_tool_use]  <-- plugin can block or modify
    |
    v
Backend Agent (Claude Code / Codex / OpenCode)
    |
    v
[TUI Event: post_tool_use]  <-- plugin can inject context
    |
    v
[TUI Event: on_error]  (if failure)
    |
    v
TUI renders response to user
```

**Key insight from the portability work:** Each backend has a different hook model (Claude Code = stdin JSON scripts, OpenCode = experimental TS plugins, Codex = nothing). The TUI event system replaces ALL of them with one unified layer. Backend-native hooks are **disabled** when running through the TUI -- the TUI handles everything.

---

## 2. Universal Event Types

### 2.1 Tool Lifecycle Events

```
pre_tool_use(event: PreToolUseEvent) -> Decision
```
Fires before the backend executes any tool. The plugin can:
- **allow** — let it proceed (default)
- **block** — prevent execution, with a reason string the agent sees
- **modify** — rewrite tool parameters before execution

```python
@dataclass
class PreToolUseEvent:
    tool: str           # "Bash", "Edit", "Write", "Read", "Grep", etc.
    params: dict        # Tool-specific parameters
    session_id: str     # Current session
    cwd: str            # Working directory
    timestamp: float    # Unix timestamp
```

---

```
post_tool_use(event: PostToolUseEvent) -> AdditionalContext | None
```
Fires after the backend completes a tool call. The plugin can:
- Return additional context the agent will see
- Fire side-effects (narration, logging, syntax checks)
- Return None to do nothing

```python
@dataclass
class PostToolUseEvent:
    tool: str           # Which tool ran
    params: dict        # What was passed in
    result: str         # Tool output (truncated to 4000 chars)
    duration_ms: int    # How long it took
    success: bool       # Did it succeed?
    session_id: str
    cwd: str
    timestamp: float
```

---

```
on_error(event: ErrorEvent) -> AdditionalContext | None
```
Fires when a tool call fails. Separate from post_tool_use to allow
specialized error handling without noise-filtering every successful call.

```python
@dataclass
class ErrorEvent:
    tool: str
    params: dict
    error: str          # Error message
    error_type: str     # "hard" (tool crashed) or "soft" (output contains error patterns)
    session_id: str
    cwd: str
    timestamp: float
```

### 2.2 Session Lifecycle Events

```
session_start(event: SessionStartEvent)
session_stop(event: SessionStopEvent)
```

```python
@dataclass
class SessionStartEvent:
    session_id: str
    backend: str        # "claude-code", "codex", "opencode"
    project_dir: str
    timestamp: float

@dataclass
class SessionStopEvent:
    session_id: str
    backend: str
    transcript_path: str | None   # Path to session log, if available
    error_count: int              # From error tracker
    duration_s: float             # Session duration
    timestamp: float
```

### 2.3 Agent Lifecycle Events

```
agent_spawn(event: AgentSpawnEvent)
agent_complete(event: AgentCompleteEvent)
```

Fires when the TUI creates or receives completion of sub-agents, background tasks, or async sessions.

```python
@dataclass
class AgentSpawnEvent:
    agent_id: str          # Unique ID for this sub-agent
    parent_session_id: str # The session that spawned it
    task: str              # What the sub-agent was asked to do
    backend: str           # Which backend it runs on
    async_: bool           # True if fire-and-forget
    timestamp: float

@dataclass
class AgentCompleteEvent:
    agent_id: str
    parent_session_id: str
    success: bool
    result_summary: str    # First 500 chars of output
    files_changed: list[str]
    duration_s: float
    timestamp: float
```

### 2.4 ADHS Timer Events

```
focus_check(event: FocusCheckEvent)
```

Fires on a configurable timer (default: every 15 minutes) when a `/focus` session is active. The TUI itself manages the timer -- no backend involvement.

```python
@dataclass
class FocusCheckEvent:
    session_id: str
    focus_goal: str        # The goal set by /focus
    elapsed_min: float     # Minutes since session/focus start
    parked_ideas: list[str]
    checkpoint_count: int  # How many checkpoints so far
    timestamp: float
```

Additional ADHS events:

```
context_degradation(event: ContextDegradationEvent)
```
Fires when the session exceeds a token/time threshold (default: 30 min or estimated 80% context window).

```python
@dataclass
class ContextDegradationEvent:
    session_id: str
    elapsed_min: float
    estimated_context_pct: float  # 0.0-1.0, estimated context usage
    suggestion: str               # "Consider /compact or /recap"
    timestamp: float
```

### 2.5 User Events

```
session_input(event: SessionInputEvent)
```
Fires when the user submits a prompt. Useful for skill routing, input logging.

```python
@dataclass
class SessionInputEvent:
    session_id: str
    text: str              # The user's input
    is_skill: bool         # True if starts with /
    skill_name: str | None # e.g., "chef", "focus"
    timestamp: float
```

---

## 3. Event Routing — Backend Mapping

The TUI intercepts the agent communication stream. For each backend, this works differently:

### 3.1 Claude Code

Claude Code has the richest native hook system. The TUI can either:

**Option A: Replace hooks (recommended)**
- Disable hooks in settings.json during TUI sessions
- TUI intercepts the same JSON stdin/stdout protocol
- TUI emits universal events from the intercepted data

**Option B: Coexist with hooks**
- Let Claude Code hooks run natively
- TUI additionally parses the output stream
- Risk: double-firing (e.g., narration from both hook and TUI plugin)

**Mapping table:**

| Universal Event | Claude Code Source |
|---|---|
| `pre_tool_use` | Hook JSON on stdin (PreToolUse event) — TUI intercepts before passing to script |
| `post_tool_use` | Hook JSON on stdin (PostToolUse event) — TUI intercepts after script runs |
| `on_error` | Hook JSON on stdin (PostToolUseFailure event) + soft-error detection in post_tool_use |
| `session_start` | TUI detects: claude process started |
| `session_stop` | Hook JSON on stdin (Stop event) or process exit |
| `agent_spawn` | TUI detects: Task tool call in stream |
| `agent_complete` | TUI detects: Task tool result in stream |
| `focus_check` | TUI timer (no Claude Code equivalent) |
| `context_degradation` | TUI timer + token estimation (no Claude Code equivalent) |

### 3.2 OpenCode

OpenCode has experimental plugins but the API is unstable. The TUI approach:

**Strategy: TUI as wrapper, bypass native plugins**
- TUI runs OpenCode via MCP or CLI
- Parses the response stream for tool calls and results
- Emits universal events
- OpenCode plugins in `~/.opencode/plugins/` are NOT needed when running through TUI

**Mapping table:**

| Universal Event | OpenCode Source |
|---|---|
| `pre_tool_use` | TUI parses outgoing tool call from agent stream |
| `post_tool_use` | TUI parses tool result from agent stream |
| `on_error` | TUI detects error in tool result + soft-error patterns |
| `session_start` | TUI detects: opencode session created |
| `session_stop` | TUI detects: opencode session idle/complete |
| `agent_spawn` | TUI detects: opencode_session_create / opencode_fire call |
| `agent_complete` | TUI detects: session status = complete |
| `focus_check` | TUI timer |
| `context_degradation` | TUI timer + token estimation |

### 3.3 Codex CLI

Codex has NO hook system, NO plugin system, and runs in a sandbox. The TUI approach:

**Strategy: TUI as orchestrator, Codex as subprocess**
- TUI spawns `codex` CLI as a child process
- Parses stdout/stderr for tool activity
- Codex's `--quiet` and `--json` flags provide structured output
- The TUI IS the hook system for Codex

**Mapping table:**

| Universal Event | Codex Source |
|---|---|
| `pre_tool_use` | TUI parses Codex JSON output for tool invocation |
| `post_tool_use` | TUI parses Codex JSON output for tool result |
| `on_error` | TUI detects error in Codex output + process exit code |
| `session_start` | TUI detects: codex process started |
| `session_stop` | TUI detects: codex process exited |
| `agent_spawn` | Not available (Codex is single-agent) |
| `agent_complete` | Not available |
| `focus_check` | TUI timer |
| `context_degradation` | Not applicable (Codex manages its own context) |

**Codex emulation notes:**
- `pre_tool_use` blocking: Codex does not support intercepting tool calls before execution. The TUI can only observe, not block. For pre-commit tests, use git hooks (`.git/hooks/pre-commit`) which Codex respects in its sandbox.
- `agent_spawn/complete`: Codex is fundamentally single-agent. These events never fire. Skills that depend on sub-agents (crew, swarm, research-swarm) are documented as non-functional in Codex (see AGENTS.codex.md).
- Error tracking: Codex does not expose structured error data. The TUI must parse free-text output for soft-error patterns (same patterns as `codex_advisor.py`).

---

## 4. Plugin Format

### 4.1 Decision: Python

**Python is the right choice for TUI plugins.** Reasoning:

| Factor | TypeScript | Python | Bash scripts |
|---|---|---|---|
| Samuel's preference | No | Yes (primary language) | Yes (for simple tasks) |
| Existing hooks | 0 of 8 | 6 of 8 | 2 of 8 |
| Runtime dependency | Node.js required | Already installed | Always available |
| Complexity handling | Good | Good | Poor for stateful logic |
| Error tracking state | Possible | Already implemented | Fragile |
| Voice daemon integration | Possible | Already implemented | Possible but ugly |
| Maintenance burden | New language for Samuel | Can maintain himself | Limited to simple cases |

The existing Python hooks (`syntax_check.py`, `pre_commit_tests.py`, `post_tool_use.py`, `stop.py`, `codex_advisor.py`, `codex_session_review.py`) already implement the core behaviors. The TUI plugin format should be a thin wrapper that calls them.

### 4.2 Plugin API

A TUI plugin is a Python file that registers event handlers:

```python
# ~/.config/myaigame-tui/plugins/syntax_checker.py

from tui_events import plugin, PostToolUseEvent

@plugin.on("post_tool_use")
def check_syntax(event: PostToolUseEvent):
    """Run py_compile on Python files after Edit/Write."""
    if event.tool not in ("Edit", "Write"):
        return None

    file_path = event.params.get("file_path", "")
    if not file_path.endswith(".py"):
        return None

    import subprocess
    result = subprocess.run(
        ["python3", "-m", "py_compile", file_path],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        error = (result.stderr or result.stdout).strip()[:500]
        return {"context": f"Syntax error in {file_path}:\n{error}"}

    return None
```

### 4.3 Plugin Registration

```python
# ~/.config/myaigame-tui/plugins/narration.py

from tui_events import plugin, PostToolUseEvent, SessionStopEvent

SKIP_TOOLS = {"Read", "Glob", "Grep", "WebSearch", "WebFetch"}
DAEMON_URL = "http://127.0.0.1:7742"

@plugin.on("post_tool_use")
def narrate_tool_result(event: PostToolUseEvent):
    """Send tool results to MultiKanalAgent for voice narration."""
    if event.tool in SKIP_TOOLS:
        return None
    if not event.result.strip():
        return None

    _send_narration(
        text=event.result[:2000],
        source=f"tui_{event.tool}",
        session_id=event.session_id,
    )
    return None  # Fire-and-forget, no context injection


@plugin.on("session_stop")
def narrate_session_end(event: SessionStopEvent):
    """Send final summary to voice daemon when session ends."""
    if not event.transcript_path:
        return

    # Reuse the existing stop.py logic
    from hooks.stop import _read_last_assistant_text
    text = _read_last_assistant_text(event.transcript_path)
    if text:
        _send_narration(text[:3000], "tui_stop", event.session_id)


def _send_narration(text: str, source: str, session_id: str):
    """Fire-and-forget HTTP POST to narration daemon."""
    import http.client, json
    try:
        conn = http.client.HTTPConnection("127.0.0.1", 7742, timeout=2)
        payload = json.dumps({"text": text, "source": source, "session_id": session_id})
        conn.request("POST", "/narrate", body=payload.encode(),
                     headers={"Content-Type": "application/json"})
        conn.close()
    except Exception:
        pass  # Daemon might not be running
```

### 4.4 Plugin Discovery

The TUI discovers plugins by scanning a directory:

```
~/.config/myaigame-tui/
    plugins/
        syntax_checker.py      # @plugin.on("post_tool_use")
        narration.py           # @plugin.on("post_tool_use", "session_stop")
        error_tracker.py       # @plugin.on("on_error", "session_stop")
        pre_commit.py          # @plugin.on("pre_tool_use")
        focus_timer.py         # @plugin.on("focus_check", "context_degradation")
    config.toml                # Plugin enable/disable, settings
```

**config.toml:**

```toml
[plugins]
# Enable/disable individual plugins
syntax_checker = true
narration = true
error_tracker = true
pre_commit = true
focus_timer = true

[narration]
daemon_host = "127.0.0.1"
daemon_port = 7742
skip_tools = ["Read", "Glob", "Grep", "WebSearch", "WebFetch"]

[focus]
check_interval_min = 15
context_degradation_min = 30

[error_tracker]
# Threshold for session-wide review warning
error_threshold = 2
```

### 4.5 Plugin Execution Model

```
Event fires
    |
    v
TUI Event Bus collects all registered handlers for this event type
    |
    v
Handlers run SEQUENTIALLY in registration order
    |
    v
If any handler returns {"block": true, "reason": "..."} for pre_tool_use:
    -> Tool call is blocked, reason sent to agent
    |
If any handler returns {"context": "..."} for post_tool_use/on_error:
    -> Additional context injected into agent's next turn
    |
Handlers that return None are side-effect-only (narration, logging)
```

**Concurrency rules:**
- `pre_tool_use` handlers run synchronously (agent waits)
- `post_tool_use` handlers with `async=True` decorator run in background thread
- `on_error` handlers run synchronously (agent should see the context)
- `session_stop` handlers run synchronously (session is ending)
- `focus_check` handlers run in TUI's own timer thread (no agent involvement)

**Timeout:** Every handler has a 10-second timeout by default. Configurable per-plugin. If a handler times out, it is killed and the event proceeds.

**Iron Rule:** A crashing plugin NEVER blocks the agent. All exceptions are caught and logged. If a plugin crashes 3 times in one session, it is disabled for that session with a warning in the TUI status bar.

---

## 5. Voice Integration

### 5.1 Current State

The MultiKanalAgent voice daemon runs on `localhost:7742`. It accepts:
- `POST /narrate` — queue text for TTS narration
- `GET /health` — check daemon status and queue size

Currently, only Claude Code integrates with it via:
- `post_tool_use.py` — sends tool results for narration (skips noisy tools)
- `stop.py` — sends final assistant message for narration

### 5.2 TUI Native Voice

In the unified TUI, voice becomes a first-class plugin rather than a per-backend hack:

```
Agent produces output
    |
    v
TUI Event Bus fires post_tool_use / session_stop
    |
    v
narration.py plugin handles the event
    |
    v
HTTP POST to MultiKanalAgent daemon (fire-and-forget)
    |
    v
Daemon queues TTS -> audio output
```

**Advantages over the current approach:**
- Works with ALL backends (not just Claude Code)
- Single narration plugin instead of 3 separate implementations
- Smart queue management: checks `/health` before sending, drops if queue > 2
- No per-backend configuration needed

### 5.3 Voice Event Extensions

The TUI can emit additional voice-relevant events that the narration plugin handles:

```python
@plugin.on("session_start")
def announce_session(event: SessionStartEvent):
    """Voice announces which backend started."""
    _send_narration(
        f"Starting session with {event.backend}.",
        "tui_session", event.session_id,
    )

@plugin.on("agent_spawn")
def announce_agent(event: AgentSpawnEvent):
    """Voice announces sub-agent creation."""
    if event.async_:
        _send_narration(
            f"Background task started: {event.task[:100]}",
            "tui_agent", event.parent_session_id,
        )

@plugin.on("agent_complete")
def announce_completion(event: AgentCompleteEvent):
    """Voice announces sub-agent completion."""
    status = "completed" if event.success else "failed"
    _send_narration(
        f"Background task {status}: {event.result_summary[:200]}",
        "tui_agent", event.parent_session_id,
    )

@plugin.on("focus_check")
def voice_focus_reminder(event: FocusCheckEvent):
    """Gentle voice reminder about focus goal."""
    _send_narration(
        f"{int(event.elapsed_min)} minutes in. Goal: {event.focus_goal}. Still on track?",
        "tui_focus", event.session_id,
    )
```

### 5.4 Voice Daemon Independence

The narration plugin is fire-and-forget. If the daemon is not running:
- All narration calls silently fail (timeout 2s, catch all exceptions)
- No error events, no retries
- TUI works identically with or without voice
- The daemon can be started/stopped independently

---

## 6. Migration Path from Existing Hooks

### 6.1 What Gets Replaced

| Existing Hook | TUI Plugin Replacement | Migration |
|---|---|---|
| `syntax_check.py` | `plugins/syntax_checker.py` | Wrap existing logic in `@plugin.on("post_tool_use")` |
| `pre_commit_tests.py` | `plugins/pre_commit.py` | Wrap existing logic in `@plugin.on("pre_tool_use")` |
| `post_tool_use.py` | `plugins/narration.py` | Wrap existing logic in `@plugin.on("post_tool_use")` |
| `stop.py` | `plugins/narration.py` | Add `@plugin.on("session_stop")` handler |
| `codex_advisor.py` | `plugins/error_tracker.py` | Wrap error tracking in `@plugin.on("on_error")`. Note: Codex CLI second-opinion calls are NOT ported -- the TUI cannot call another AI from a plugin (same limitation as OpenCode). The error tracking and threshold alerts ARE ported. |
| `codex_session_review.py` | `plugins/error_tracker.py` | Session-end error review in `@plugin.on("session_stop")` |
| `gather-context.sh` | Not a plugin -- used by skills directly | Skills call it via `{{gather_context()}}` or shell. No change needed. |
| `gather-context-enhanced.sh` | Same as above | No change needed. |
| `session-extract.sh` | Not a plugin -- manual utility | No change needed. |

### 6.2 What Gets Added (New in TUI)

| New Plugin | Event | Purpose |
|---|---|---|
| `focus_timer.py` | `focus_check`, `context_degradation` | ADHS timer support (no equivalent in any current backend) |
| `session_logger.py` | `session_start`, `session_stop`, `session_input` | Unified session logging across all backends |
| `agent_monitor.py` | `agent_spawn`, `agent_complete` | Track sub-agents, prevent zombie processes |

### 6.3 Backward Compatibility

When running WITHOUT the TUI (direct Claude Code / OpenCode / Codex):
- The existing hooks in `portable/hooks/` still work as-is
- The OpenCode plugins in `portable/opencode/plugins/` still work
- Codex still has no hooks (uses git hooks for pre-commit)
- Nothing breaks -- the TUI plugins are an additional layer, not a replacement for standalone use

When running WITH the TUI:
- Backend-native hooks should be disabled to prevent double-firing
- The TUI manages this: it sets `MYAIGAME_TUI_ACTIVE=1` env var
- Existing hooks can check this env var and skip if TUI is active:

```python
# Add to existing hooks for coexistence:
import os
if os.environ.get("MYAIGAME_TUI_ACTIVE") == "1":
    sys.exit(0)  # TUI handles this event
```

---

## 7. Event Bus Implementation Sketch

```python
# tui_events.py — Core event bus for the unified TUI

import importlib
import inspect
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("tui.events")

PLUGIN_DIR = Path.home() / ".config" / "myaigame-tui" / "plugins"
HANDLER_TIMEOUT = 10  # seconds
MAX_CRASHES = 3


class PluginRegistry:
    """Decorator-based plugin registration."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, event_type: str):
        """Decorator to register a handler for an event type."""
        def decorator(fn: Callable):
            self._handlers.setdefault(event_type, []).append(fn)
            return fn
        return decorator


# Global registry — plugins import this
plugin = PluginRegistry()


class EventBus:
    """Dispatches events to registered plugin handlers."""

    def __init__(self):
        self._crash_counts: dict[str, int] = {}  # plugin_name -> crash count
        self._disabled: set[str] = set()

    def load_plugins(self):
        """Scan plugin directory and import all .py files."""
        if not PLUGIN_DIR.exists():
            log.info("No plugin directory at %s", PLUGIN_DIR)
            return

        for py_file in sorted(PLUGIN_DIR.glob("*.py")):
            name = py_file.stem
            if name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(name, py_file)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                log.info("Loaded plugin: %s", name)
            except Exception as e:
                log.error("Failed to load plugin %s: %s", name, e)

    def emit(self, event_type: str, event: Any) -> list[dict]:
        """Emit an event. Returns list of handler responses (non-None)."""
        handlers = plugin._handlers.get(event_type, [])
        responses = []

        for handler in handlers:
            plugin_name = handler.__module__ or handler.__qualname__
            if plugin_name in self._disabled:
                continue

            try:
                result = self._run_with_timeout(handler, event)
                if result is not None:
                    responses.append(result)
            except TimeoutError:
                log.warning("Plugin %s timed out on %s", plugin_name, event_type)
                self._record_crash(plugin_name)
            except Exception as e:
                log.error("Plugin %s crashed on %s: %s", plugin_name, event_type, e)
                self._record_crash(plugin_name)

        return responses

    def _run_with_timeout(self, fn: Callable, event: Any, timeout: float = HANDLER_TIMEOUT):
        """Run handler with timeout. Raises TimeoutError if exceeded."""
        result = [None]
        error = [None]

        def target():
            try:
                result[0] = fn(event)
            except Exception as e:
                error[0] = e

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            raise TimeoutError(f"{fn.__qualname__} exceeded {timeout}s")
        if error[0]:
            raise error[0]
        return result[0]

    def _record_crash(self, plugin_name: str):
        """Track crashes. Disable plugin after MAX_CRASHES."""
        self._crash_counts[plugin_name] = self._crash_counts.get(plugin_name, 0) + 1
        if self._crash_counts[plugin_name] >= MAX_CRASHES:
            self._disabled.add(plugin_name)
            log.warning("Plugin %s disabled after %d crashes", plugin_name, MAX_CRASHES)
```

---

## 8. Comparison: What Each Backend Actually Gets

| Capability | Claude Code (standalone) | Codex (standalone) | OpenCode (standalone) | TUI (any backend) |
|---|---|---|---|---|
| pre_tool_use blocking | Yes (native hooks) | No | Experimental | Yes (plugin) |
| post_tool_use context | Yes (native hooks) | No | Experimental | Yes (plugin) |
| Syntax checking | Yes (hook) | Git hook only | Experimental plugin | Yes (plugin) |
| Pre-commit tests | Yes (hook) | Git hook only | Experimental plugin | Yes (plugin) |
| Voice narration | Yes (hook) | No | Experimental plugin | Yes (plugin, native) |
| Session-end narration | Yes (hook) | No | No | Yes (plugin) |
| Error tracking | Yes (hook + Codex CLI) | No | Experimental plugin | Yes (plugin) |
| Error pattern review | Yes (hook + Codex CLI) | No | No | Yes (plugin) |
| Focus timer | No | No | No | **Yes (new)** |
| Context degradation | No | No | No | **Yes (new)** |
| Agent monitoring | No | No | No | **Yes (new)** |
| Session logging | No | No | No | **Yes (new)** |

The TUI event system is the great equalizer: every backend gets the same capabilities, plus new ones that don't exist anywhere today.

---

## 9. Open Questions

1. **Plugin language enforcement:** Should we ONLY allow Python plugins, or also support bash scripts for simple one-liners? Bash would be simpler for things like "run a command after every commit" but harder to pass structured event data. **Recommendation:** Python-only for plugins, but plugins can call bash scripts internally.

2. **Codex pre_tool_use limitation:** Codex cannot be intercepted before tool execution. Should the TUI warn when a `pre_tool_use` blocking plugin is active but the backend is Codex? **Recommendation:** Yes, log a warning at session start.

3. **Second-opinion AI calls:** The `codex_advisor.py` hook calls Codex CLI for error analysis. In the TUI, should error_tracker.py call a different AI? Or just provide structured error data without AI analysis? **Recommendation:** No AI calls from plugins. The TUI agent itself should handle error recovery based on the structured context the plugin provides.

4. **Plugin hot-reload:** Should plugins be reloadable without restarting the TUI? **Recommendation:** Nice-to-have for v2. For v1, restart required.
