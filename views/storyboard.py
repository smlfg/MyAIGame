import streamlit as st

from data.models import AgentEvent
from components.shared import format_cost, format_tokens, format_timestamp


def render():
    """Narrative markdown view with Mermaid diagram"""
    st.title("📖 Storyboard")
    st.markdown("Event narrative and delegation flow")

    events = st.session_state.get("events", [])

    if not events:
        st.warning("No events to display")
        return

    # Stats header
    total_cost = sum(e.cost_usd for e in events)
    total_tokens = sum(e.tokens_in + e.tokens_out for e in events)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cost", format_cost(total_cost))
    with col2:
        st.metric("Total Tokens", format_tokens(total_tokens))
    with col3:
        st.metric("Events", len(events))

    st.divider()

    # Generate narrative
    narrative = generate_narrative(events)

    st.subheader("Timeline")
    st.markdown(narrative)

    # Mermaid diagram
    st.divider()
    st.subheader("Delegation Flow")

    mermaid = generate_mermaid(events)
    st.markdown(f"```mermaid\n{mermaid}\n```")

    # Export
    export_content = f"""# Session Storyboard

## Stats
- Total Cost: {format_cost(total_cost)}
- Total Tokens: {format_tokens(total_tokens)}
- Events: {len(events)}

---

{narrative}

---

```mermaid
{mermaid}
```
"""

    st.download_button(
        label="📥 Export as Markdown",
        data=export_content,
        file_name="storyboard.md",
        mime="text/markdown",
    )


def generate_narrative(events: list[AgentEvent]) -> str:
    """Convert events to human-readable markdown"""
    lines = []

    sorted_events = sorted(events, key=lambda e: e.timestamp)

    for e in sorted_events:
        ts = format_timestamp(e.timestamp)

        if e.event_type == "user_msg":
            lines.append(f"- **{ts}** — 👤 User message")

        elif e.event_type == "assistant_msg":
            tokens = e.tokens_in + e.tokens_out
            lines.append(
                f"- **{ts}** — **{e.agent.upper()}** responded "
                f"({format_tokens(tokens)} tokens, {format_cost(e.cost_usd)})"
            )

        elif e.event_type == "tool_call":
            lines.append(
                f"- **{ts}** — 🔧 **{e.agent.upper()}** called `{e.tool_name or 'unknown'}`"
            )

    return "\n".join(lines) if lines else "_No events_"


def generate_mermaid(events: list[AgentEvent]) -> str:
    """Generate Mermaid sequence diagram from events"""
    lines = ["sequenceDiagram"]

    # Track active participants
    participants = set(["User"])

    sorted_events = sorted(events, key=lambda e: e.timestamp)

    # Add participants
    for e in sorted_events:
        if e.agent and e.agent not in participants:
            participants.add(e.agent)

    # Add participant declarations
    for p in sorted(participants):
        if p != "User":
            lines.append(f"    participant {p.capitalize()}")
    lines.append("    participant User")
    lines.append("")

    # Add interactions
    prev_agent = None
    for e in sorted_events:
        if e.event_type == "user_msg":
            lines.append(f"    User->>{e.agent.capitalize()}: message")
            prev_agent = e.agent

        elif e.event_type == "tool_call" and e.tool_name:
            if prev_agent:
                lines.append(
                    f"    {prev_agent.capitalize()}->>{e.agent.capitalize()}: {e.tool_name}()"
                )

        elif e.event_type == "assistant_msg":
            tokens = e.tokens_in + e.tokens_out
            lines.append(
                f"    {e.agent.capitalize()}-->>User: response ({format_tokens(tokens)} tokens)"
            )
            prev_agent = None

    return "\n".join(lines)
