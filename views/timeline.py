import streamlit as st
import plotly.express as px
import pandas as pd

from data.models import AgentEvent
from components.shared import agent_color_map, format_cost, format_tokens


def render():
    """Swimlane timeline using Plotly"""
    st.title("📊 Timeline")
    st.markdown("Agent activity swimlane")

    events = st.session_state.get("events", [])

    if not events:
        st.warning("No events to display")
        return

    # Prepare dataframe
    rows = []
    for e in events:
        start = e.timestamp
        # Default duration 1 second if not specified
        duration = (e.duration_ms / 1000) if e.duration_ms else 1
        end = start + pd.Timedelta(seconds=duration)

        hover_text = f"""
        <b>{e.event_type}</b><br>
        Tool: {e.tool_name or "N/A"}<br>
        Tokens In: {format_tokens(e.tokens_in)}<br>
        Tokens Out: {format_tokens(e.tokens_out)}<br>
        Cost: {format_cost(e.cost_usd)}<br>
        {e.content_preview[:100] if e.content_preview else ""}
        """

        rows.append(
            {
                "Task": e.agent,
                "Start": start,
                "Finish": end,
                "Agent": e.agent,
                "Event": e.event_type,
                "Tool": e.tool_name or "",
                "Tokens In": e.tokens_in,
                "Tokens Out": e.tokens_out,
                "Cost": e.cost_usd,
                "Duration": duration,
                "Hover": hover_text,
            }
        )

    df = pd.DataFrame(rows)

    colors = agent_color_map()

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Agent",
        color="Agent",
        hover_data={"Task": False, "Start": False, "Finish": False},
        color_discrete_map=colors,
        title="Agent Activity Timeline",
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        xaxis_title="Time", yaxis_title="Agent", height=400, showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # Event list
    st.subheader("Events")

    for e in sorted(events, key=lambda x: x.timestamp, reverse=True)[:20]:
        with st.expander(
            f"{e.timestamp.strftime('%H:%M:%S')} — {e.agent.upper()} — {e.event_type}"
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tokens In", format_tokens(e.tokens_in))
            with col2:
                st.metric("Tokens Out", format_tokens(e.tokens_out))
            with col3:
                st.metric("Cost", format_cost(e.cost_usd))

            if e.tool_name:
                st.caption(f"**Tool:** {e.tool_name}")
            if e.content_preview:
                st.caption(f"**Preview:** {e.content_preview[:200]}")
