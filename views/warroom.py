import streamlit as st
from datetime import datetime, timezone, timedelta

from data.models import AgentEvent
from components.shared import (
    format_cost,
    format_tokens,
    format_relative_time,
    agent_color_map,
    format_timestamp,
)


def render():
    """War Room — 5 columns, one per agent type, live status"""
    st.title("🤖 War Room")
    st.markdown("Live agent monitoring and status")

    events = st.session_state.get("events", [])

    if not events:
        st.warning("No events yet. Waiting for data...")
        return

    # Aggregate stats
    total_cost = sum(e.cost_usd for e in events)
    total_tokens_in = sum(e.tokens_in for e in events)
    total_tokens_out = sum(e.tokens_out for e in events)

    # Session duration
    if events:
        first_ts = min(e.timestamp for e in events)
        last_ts = max(e.timestamp for e in events)
        duration = (last_ts - first_ts).total_seconds()
        duration_str = f"{int(duration / 60)}m {int(duration % 60)}s"
    else:
        duration_str = "0m"

    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Cost", format_cost(total_cost))
    with col2:
        st.metric(
            "Tokens (In/Out)",
            f"{format_tokens(total_tokens_in)} / {format_tokens(total_tokens_out)}",
        )
    with col3:
        st.metric("Events", len(events))
    with col4:
        st.metric("Duration", duration_str)

    st.divider()

    # Agent cards
    agent_types = ["opus", "sonnet", "haiku", "flash", "minimax"]
    colors = agent_color_map()
    cols = st.columns(5)

    now = datetime.now(timezone.utc)

    for idx, agent in enumerate(agent_types):
        with cols[idx]:
            # Get events for this agent
            agent_events = [e for e in events if e.agent == agent]

            if not agent_events:
                st.markdown(f"**{agent.upper()}**")
                st.markdown("🟢 Idle")
                st.caption("No activity")
                continue

            # Check if active (last event < 30s ago)
            last_event = max(agent_events, key=lambda e: e.timestamp)
            is_active = (now - last_event).total_seconds() < 30

            # Stats
            agent_cost = sum(e.cost_usd for e in agent_events)
            agent_tokens_in = sum(e.tokens_in for e in agent_events)
            agent_tokens_out = sum(e.tokens_out for e in agent_events)

            # Color indicator
            color = colors.get(agent, "#888")
            status = "🔴 Active" if is_active else "🟢 Idle"

            st.markdown(f"**{agent.upper()}** {status}")
            st.metric("Cost", format_cost(agent_cost))
            st.caption(f"Tokens: {format_tokens(agent_tokens_in + agent_tokens_out)}")

            # Last action
            last_tool = last_event.tool_name or last_event.event_type
            st.caption(
                f"Last: {last_tool} ({format_relative_time(last_event.timestamp)})"
            )

            # Expander with recent events
            with st.expander("Recent"):
                recent = sorted(agent_events, key=lambda e: e.timestamp, reverse=True)[
                    :5
                ]
                for e in recent:
                    tool = e.tool_name or e.event_type
                    st.caption(f"{format_timestamp(e.timestamp)} — {tool}")
