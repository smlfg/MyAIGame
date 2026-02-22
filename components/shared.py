import streamlit as st
from datetime import datetime, timezone
from typing import Optional
import pytz

AGENT_COLORS = {
    "opus": "#FF6B6B",
    "sonnet": "#4ECDC4",
    "haiku": "#45B7D1",
    "flash": "#F7DC6F",
    "minimax": "#BB8FCE",
}


def session_picker(sessions: dict) -> tuple[Optional[str], Optional[str]]:
    """Sidebar selectbox for session selection (grouped by source)"""
    options = []
    labels = {}

    if sessions.get("claude"):
        for s in sessions["claude"]:
            key = f"claude:{s['path']}"
            options.append(key)
            labels[key] = f"Claude: {s['name']}"

    if sessions.get("opencode"):
        for s in sessions["opencode"]:
            key = f"opencode:{s['id']}"
            options.append(key)
            title = s.get("title", "Untitled")
            labels[key] = f"OpenCode: {title[:30]}"

    if not options:
        return None, None

    selected = st.sidebar.selectbox(
        "Session", options, format_func=lambda x: labels.get(x, x)
    )

    if selected:
        if selected.startswith("claude:"):
            return selected.replace("claude:", ""), None
        elif selected.startswith("opencode:"):
            return None, selected.replace("opencode:", "")

    return None, None


def auto_refresh_toggle() -> tuple[bool, int]:
    """Toggle + interval slider for auto-refresh"""
    enabled = st.sidebar.toggle("Auto-refresh", value=True)
    interval = 3
    if enabled:
        interval = st.sidebar.slider("Refresh interval (s)", 1, 10, 3)
    return enabled, interval


def time_range_filter() -> Optional[tuple[datetime, datetime]]:
    """Date/time range filter"""
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=None)
    with col2:
        end_date = st.date_input("End date", value=None)

    if start_date and end_date:
        local_tz = pytz.timezone("Europe/Berlin")
        start = datetime.combine(start_date, datetime.min.time()).replace(
            tzinfo=local_tz
        )
        end = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=local_tz)
        return (start, end)
    return None


def agent_color_map() -> dict:
    """Consistent colors per agent"""
    return AGENT_COLORS.copy()


def format_cost(usd: float) -> str:
    """Format as $0.0042 etc"""
    if usd < 0.001:
        return f"${usd:.6f}"
    elif usd < 1:
        return f"${usd:.4f}"
    else:
        return f"${usd:.2f}"


def format_tokens(n: int) -> str:
    """Format as 1.2K, 45.6K etc"""
    if n < 1000:
        return str(n)
    elif n < 1000000:
        return f"{n / 1000:.1f}K"
    else:
        return f"{n / 1000000:.1f}M"


def format_timestamp(ts: datetime) -> str:
    """Format timestamp for display"""
    local_tz = pytz.timezone("Europe/Berlin")
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ts_local = ts.astimezone(local_tz)
    return ts_local.strftime("%H:%M:%S")


def format_relative_time(ts: datetime) -> str:
    """Format as relative time like '30s ago'"""
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    delta = now - ts
    seconds = delta.total_seconds()

    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    else:
        return f"{int(seconds / 3600)}h ago"
