"""Claude Code hook-based adapter.

Captures agent output via Claude Code's hook system:
- Stop event: fires when agent produces a final response
- PostToolUse event: fires after each tool invocation

Hook scripts receive JSON on stdin and must exit 0
to avoid blocking the agent (the Iron Rule).
"""

import json
import logging
import pathlib
import shutil
import sys

from .base import BaseAdapter

logger = logging.getLogger("multikanal.adapters.claude_hook")

# Default hooks directory for Claude Code
_CLAUDE_HOOKS_DIR = pathlib.Path.home() / ".claude"


class ClaudeHookAdapter(BaseAdapter):
    """Processes Claude Code hook events and sends to daemon."""

    def capture(self, **kwargs) -> str:
        """Read hook event from stdin and extract text content."""
        raw = kwargs.get("stdin_data") or ""
        if not raw:
            try:
                raw = sys.stdin.read()
            except Exception:
                return ""

        return self._extract_text(raw)

    def _extract_text(self, raw_json: str) -> str:
        """Extract human-readable text from a Claude Code hook event."""
        try:
            data = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            return ""

        # Stop event: contains the final assistant response
        if "stop_response" in data:
            return self._extract_from_stop(data)

        # PostToolUse event: contains tool result
        if "tool_use" in data or "tool_name" in data:
            return self._extract_from_tool(data)

        # Generic: try to find any text content
        for key in ("text", "content", "message", "output", "result"):
            if key in data and isinstance(data[key], str):
                return data[key]

        return ""

    def _extract_from_stop(self, data: dict) -> str:
        """Extract text from a Stop hook event."""
        response = data.get("stop_response", {})

        # Response may contain content blocks
        if isinstance(response, dict):
            content = response.get("content", [])
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                if texts:
                    return "\n".join(texts)

            # Direct text field
            text = response.get("text", "")
            if text:
                return text

        if isinstance(response, str):
            return response

        return ""

    def _extract_from_tool(self, data: dict) -> str:
        """Extract text from a PostToolUse hook event."""
        tool_name = data.get("tool_name", data.get("name", "unknown"))
        result = data.get("tool_result", data.get("result", ""))

        if isinstance(result, dict):
            # Try common result fields
            for key in ("content", "text", "output", "stdout"):
                if key in result and isinstance(result[key], str):
                    result = result[key]
                    break
            else:
                result = json.dumps(result)

        if isinstance(result, str) and result.strip():
            return f"Tool '{tool_name}' result:\n{result}"

        return ""


def process_hook_event(event_type: str = "stop"):
    """Entry point for hook scripts. Reads stdin, sends to daemon.

    Always exits 0 — the Iron Rule.
    """
    try:
        adapter = ClaudeHookAdapter()
        text = adapter.capture()
        if text:
            adapter.send_to_daemon(text, source=f"claude_{event_type}")
    except Exception:
        pass  # Iron Rule: never fail
    sys.exit(0)


def install_hooks(target_dir: str | None = None):
    """Install Claude Code hooks configuration.

    Creates/updates .claude/hooks.json to point at our hook scripts.
    """
    hooks_dir = pathlib.Path(target_dir) if target_dir else _CLAUDE_HOOKS_DIR
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hooks_json = hooks_dir / "hooks.json"

    # Find our plugin hook scripts
    plugin_dir = pathlib.Path(__file__).resolve().parents[2] / "plugins" / "claude-hook" / "hooks"

    hooks_config = {
        "hooks": {
            "Stop": [
                {
                    "type": "command",
                    "command": f"{sys.executable} {plugin_dir / 'stop.py'}",
                }
            ],
            "PostToolUse": [
                {
                    "type": "command",
                    "command": f"{sys.executable} {plugin_dir / 'post_tool_use.py'}",
                }
            ],
        }
    }

    # If hooks.json exists, merge rather than overwrite
    if hooks_json.exists():
        try:
            existing = json.loads(hooks_json.read_text(encoding="utf-8"))
            existing_hooks = existing.get("hooks", {})
            for event, handlers in hooks_config["hooks"].items():
                if event not in existing_hooks:
                    existing_hooks[event] = handlers
                else:
                    # Add our handlers if not already present
                    existing_cmds = {h.get("command") for h in existing_hooks[event]}
                    for h in handlers:
                        if h["command"] not in existing_cmds:
                            existing_hooks[event].append(h)
            existing["hooks"] = existing_hooks
            hooks_config = existing
        except Exception:
            pass  # Overwrite if can't parse

    hooks_json.write_text(json.dumps(hooks_config, indent=2), encoding="utf-8")
    print(f"Hooks installed to {hooks_json}")
