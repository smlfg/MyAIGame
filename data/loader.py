from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from data.models import AgentEvent
from data import claude_watcher, opencode_poller


def load_events(
    claude_session: Optional[str] = None,
    opencode_session: Optional[str] = None,
    time_range: Optional[tuple[datetime, datetime]] = None,
) -> list[AgentEvent]:
    """Load and merge events from both sources, sorted by timestamp."""
    events = []

    # Load Claude sessions
    if claude_session:
        path = Path(claude_session)
        if path.exists():
            claude_events, _ = claude_watcher.parse_session(path, offset=0)
            events.extend(claude_events)
    else:
        active = claude_watcher.find_active_session()
        if active:
            claude_events, _ = claude_watcher.parse_session(active, offset=0)
            events.extend(claude_events)

    # Load OpenCode sessions
    if opencode_session:
        opencode_events = opencode_poller.parse_session_messages(opencode_session)
        events.extend(opencode_events)
    else:
        active_sessions = opencode_poller.find_active_sessions(minutes=60)
        for sess in active_sessions:
            sess_id = sess.get("id", "")
            if sess_id:
                opencode_events = opencode_poller.parse_session_messages(sess_id)
                events.extend(opencode_events)

    # Filter by time range if provided
    if time_range:
        start, end = time_range
        events = [e for e in events if start <= e.timestamp <= end]

    events.sort(key=lambda e: e.timestamp)
    return events


def get_session_list() -> dict:
    """Returns dict with 'claude' and 'opencode' session lists"""
    result = {"claude": [], "opencode": []}

    claude_sessions = claude_watcher.find_all_sessions()
    result["claude"] = [{"path": str(p), "name": p.name} for p in claude_sessions]

    opencode_sessions = opencode_poller.find_sessions()
    result["opencode"] = [
        {
            "id": s.get("id", ""),
            "title": s.get("title", "Untitled"),
            "updated": s.get("time", {}).get("updated", 0),
        }
        for s in opencode_sessions
    ]

    return result


def get_active_events(refresh_interval: int = 2) -> list[AgentEvent]:
    """For live mode, uses offsets to only read new data"""
    import streamlit as st

    events = []

    if "claude_offsets" not in st.session_state:
        st.session_state.claude_offsets = {}

    if "opencode_offsets" not in st.session_state:
        st.session_state.opencode_offsets = {}

    active_claude = claude_watcher.find_active_session()
    if active_claude:
        path_str = str(active_claude)
        offset = st.session_state.claude_offsets.get(path_str, 0)
        claude_events, new_offset = claude_watcher.parse_session(active_claude, offset)
        st.session_state.claude_offsets[path_str] = new_offset
        events.extend(claude_events)

    active_opencode = opencode_poller.find_active_sessions(minutes=10)
    for sess in active_opencode:
        sess_id = sess.get("id", "")
        if sess_id:
            opencode_events = opencode_poller.parse_session_messages(sess_id)
            events.extend(opencode_events)

    events.sort(key=lambda e: e.timestamp)
    return events
