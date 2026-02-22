import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import timedelta

from data.models import AgentEvent
from components.shared import format_cost, format_tokens, agent_color_map


def render():
    """Three sub-views: Sankey, Cumulative Cost, Heatmap"""
    st.title("💰 Cost Analysis")

    events = st.session_state.get("events", [])

    if not events:
        st.warning("No events to analyze")
        return

    tab1, tab2, tab3 = st.tabs(["Sankey Diagram", "Cumulative Cost", "Heatmap"])

    with tab1:
        render_sankey(events)
    with tab2:
        render_cumulative(events)
    with tab3:
        render_heatmap(events)


def render_sankey(events: list[AgentEvent]):
    """Sankey showing agent interactions"""
    st.subheader("Cost Flow")

    # Group by source->target from delegations
    # For now, show User -> Agent flows

    agents = list(set(e.agent for e in events if e.agent))
    all_nodes = ["User"] + agents

    node_map = {name: idx for idx, name in enumerate(all_nodes)}

    # Build links: User -> Agent (based on who responded)
    links = {}
    for e in events:
        if e.event_type == "assistant_msg" and e.tokens_out > 0:
            key = ("User", e.agent)
            links[key] = links.get(key, 0) + e.tokens_out

    source_indices = []
    target_indices = []
    values = []

    for (src, tgt), val in links.items():
        source_indices.append(node_map[src])
        target_indices.append(node_map[tgt])
        values.append(val)

    if not source_indices:
        st.info("Not enough delegation data for Sankey")
        return

    colors = agent_color_map()
    node_colors = ["#888888"] + [colors.get(a, "#888") for a in agents]
    link_colors = ["rgba(100,200,100,0.4)"] * len(source_indices)

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=all_nodes,
                    color=node_colors,
                ),
                link=dict(
                    source=source_indices,
                    target=target_indices,
                    value=values,
                    color=link_colors,
                ),
            )
        ]
    )

    fig.update_layout(title_text="Token Flow (User → Agents)", height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_cumulative(events: list[AgentEvent]):
    """Cumulative cost timeline stacked by agent"""
    st.subheader("Cumulative Cost Over Time")

    if not events:
        return

    df = pd.DataFrame(
        [
            {"timestamp": e.timestamp, "agent": e.agent, "cost": e.cost_usd}
            for e in events
        ]
    )

    if df.empty:
        return

    df = df.sort_values("timestamp")
    df["cumcost"] = df.groupby("agent")["cost"].cumsum()

    colors = agent_color_map()

    agents = df["agent"].unique()

    fig = go.Figure()
    for agent in agents:
        agent_df = df[df["agent"] == agent]
        fig.add_trace(
            go.Scatter(
                x=agent_df["timestamp"],
                y=agent_df["cumcost"],
                mode="lines",
                stackgroup="one",
                name=agent,
                fillcolor=colors.get(agent, "#888"),
                line=dict(width=0),
            )
        )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Cumulative Cost (USD)",
        height=400,
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_heatmap(events: list[AgentEvent]):
    """Cost heatmap by time buckets and agent"""
    st.subheader("Cost Heatmap (5-min buckets)")

    if not events:
        return

    # Create 5-minute buckets
    df = pd.DataFrame(
        [
            {"timestamp": e.timestamp, "agent": e.agent, "cost": e.cost_usd}
            for e in events
        ]
    )

    if df.empty:
        return

    df["bucket"] = df["timestamp"].dt.floor("5min")

    heatmap_data = df.groupby(["bucket", "agent"])["cost"].sum().reset_index()

    pivot = heatmap_data.pivot(index="agent", columns="bucket", values="cost").fillna(0)

    colors = agent_color_map()

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Blues",
            colorbar=dict(title="Cost (USD)"),
        )
    )

    fig.update_layout(xaxis_title="Time Bucket", yaxis_title="Agent", height=400)

    st.plotly_chart(fig, use_container_width=True)
