import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import glob

from data.models import AgentEvent
from data.pricing import calc_cost, model_to_agent


def find_active_session() -> Optional[Path]:
    """Find newest .jsonl in ~/.claude/projects/*/"""
    home = Path.home()
    patterns = [
        home / ".claude/projects" / "*" / "*.jsonl",
    ]

    candidates = []
    for pattern in patterns:
        candidates.extend(glob.glob(str(pattern), recursive=False))

    if not candidates:
        return None

    # Sort by mtime, newest first
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return Path(candidates[0])


def find_all_sessions() -> list[Path]:
    """List all .jsonl files sorted by mtime"""
    home = Path.home()
    pattern = home / ".claude/projects" / "*" / "*.jsonl"

    candidates = glob.glob(str(pattern), recursive=False)
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return [Path(p) for p in candidates]


def parse_session(path: Path, offset: int = 0) -> tuple[list[AgentEvent], int]:
    """Read from byte offset, return (events, new_offset)"""
    events = []

    try:
        new_offset = offset
        with open(path, "r", encoding="utf-8") as f:
            f.seek(offset)

            while True:
                line = f.readline()
                if not line:
                    break

                new_offset = f.tell()

                try:
                    data = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                # Skip file-history-snapshot
                if data.get("type") == "file-history-snapshot":
                    continue

                session_id = data.get("sessionId", "")
                ts_str = data.get("timestamp", "")

                try:
                    if ts_str:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    else:
                        ts = datetime.now(timezone.utc)
                except Exception:
                    ts = datetime.now(timezone.utc)

                msg_type = data.get("type", "")

                if msg_type == "user":
                    content = ""
                    if isinstance(data.get("message", {}).get("content"), str):
                        content = data["message"]["content"]
                    elif isinstance(data.get("message", {}).get("content"), list):
                        for block in data["message"]["content"]:
                            if isinstance(block, dict):
                                content += block.get("text", "")

                    event = AgentEvent(
                        timestamp=ts,
                        session_id=session_id,
                        agent="sonnet",
                        event_type="user_msg",
                        tokens_in=0,
                        tokens_out=0,
                        cost_usd=0.0,
                        content_preview=content[:200] if content else "",
                        source="claude",
                    )
                    events.append(event)

                elif msg_type == "assistant":
                    message = data.get("message", {})
                    model = message.get("model", "sonnet")
                    agent = model_to_agent(model)

                    usage = message.get("usage", {})
                    tokens_in = usage.get("input_tokens", 0)
                    tokens_out = usage.get("output_tokens", 0)
                    cost = calc_cost(agent, tokens_in, tokens_out)

                    # Extract content
                    content_parts = []
                    tool_name = None
                    if isinstance(message.get("content"), list):
                        for block in message["content"]:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    content_parts.append(block.get("text", ""))
                                elif block.get("type") == "tool_use":
                                    tool_name = block.get("name", "unknown")
                                    tool_id = block.get("id", "")

                                    # Create tool_call event
                                    tool_event = AgentEvent(
                                        timestamp=ts,
                                        session_id=session_id,
                                        agent=agent,
                                        event_type="tool_call",
                                        tokens_in=0,
                                        tokens_out=0,
                                        cost_usd=0.0,
                                        tool_name=tool_name,
                                        parent_event_id=tool_id,
                                        source="claude",
                                    )
                                    events.append(tool_event)

                    content_preview = (
                        " ".join(content_parts)[:200] if content_parts else ""
                    )

                    event = AgentEvent(
                        timestamp=ts,
                        session_id=session_id,
                        agent=agent,
                        event_type="assistant_msg",
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        cost_usd=cost,
                        content_preview=content_preview,
                        source="claude",
                    )
                    events.append(event)

            return events, new_offset

    except Exception as e:
        print(f"Error parsing session {path}: {e}")
        return events, offset
