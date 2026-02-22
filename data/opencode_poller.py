import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

from data.models import AgentEvent
from data.pricing import calc_cost, model_to_agent


STORAGE_ROOT = Path.home() / ".local/share/opencode/storage"


def find_sessions() -> list[dict]:
    """Glob session/**/*.json, parse, sort by time.updated desc"""
    sessions = []

    if not STORAGE_ROOT.exists():
        return sessions

    session_dir = STORAGE_ROOT / "session"
    if not session_dir.exists():
        return sessions

    try:
        for session_file in session_dir.rglob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append(data)
            except Exception:
                continue
    except Exception:
        pass

    sessions.sort(key=lambda s: s.get("time", {}).get("updated", 0), reverse=True)
    return sessions


def find_active_sessions(minutes: int = 10) -> list[dict]:
    """Filter to sessions updated in last N minutes"""
    cutoff = (
        datetime.now(timezone.utc) - timedelta(minutes=minutes)
    ).timestamp() * 1000
    return [s for s in find_sessions() if s.get("time", {}).get("updated", 0) > cutoff]


def parse_session_messages(session_id: str) -> list[AgentEvent]:
    """Read all messages from message/<session_id>/*.json"""
    events = []

    if not STORAGE_ROOT.exists():
        return events

    message_dir = STORAGE_ROOT / "message" / session_id
    if not message_dir.exists():
        return events

    try:
        message_files = list(message_dir.glob("*.json"))
        messages = []

        for msg_file in message_files:
            try:
                with open(msg_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    messages.append(data)
            except Exception:
                continue

        messages.sort(key=lambda m: m.get("time", {}).get("created", 0))

        for msg in messages:
            role = msg.get("role", "")
            time_data = msg.get("time", {})
            created = time_data.get("created", 0)
            completed = time_data.get("completed", created)

            try:
                ts = datetime.fromtimestamp(created / 1000, tz=timezone.utc)
            except Exception:
                ts = datetime.now(timezone.utc)

            duration_ms = int(completed - created) if completed and created else None

            if role == "user":
                event = AgentEvent(
                    timestamp=ts,
                    session_id=session_id,
                    agent="sonnet",
                    event_type="user_msg",
                    tokens_in=0,
                    tokens_out=0,
                    cost_usd=0.0,
                    duration_ms=duration_ms,
                    source="opencode",
                )
                events.append(event)

            elif role == "assistant":
                model_id = msg.get("modelID", "sonnet")
                agent = model_to_agent(model_id)

                tokens_data = msg.get("tokens", {})
                tokens_in = tokens_data.get("input", 0)
                tokens_out = tokens_data.get("output", 0)
                cost = msg.get("cost", 0)

                if cost == 0 and (tokens_in or tokens_out):
                    cost = calc_cost(agent, tokens_in, tokens_out)

                finish = msg.get("finish", "stop")

                if finish == "tool-calls":
                    event_type = "tool_call"
                else:
                    event_type = "assistant_msg"

                event = AgentEvent(
                    timestamp=ts,
                    session_id=session_id,
                    agent=agent,
                    event_type=event_type,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost_usd=cost,
                    duration_ms=duration_ms,
                    source="opencode",
                )
                events.append(event)

    except Exception as e:
        print(f"Error parsing opencode messages: {e}")

    return events
