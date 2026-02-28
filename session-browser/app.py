"""
Claude Code Session Browser — "Wo war ich?" Dashboard
2x5 Grid der letzten 10 grossen Sessions zum Wiedereinstieg.
"""

import re
import streamlit as st
from datetime import datetime, timedelta, timezone
from session_parser import (
    quick_parse_all,
    full_parse_session,
    search_sessions,
    get_all_projects,
    format_size,
    parse_timestamp,
)

st.set_page_config(
    page_title="Wo war ich?",
    layout="wide",
    page_icon="\U0001f680",
    initial_sidebar_state="collapsed",
)


# --- Data Loading ---
@st.cache_data(ttl=60)
def load_sessions():
    return quick_parse_all()


@st.cache_data(ttl=120)
def load_full_session(filepath: str):
    return full_parse_session(filepath)


def time_ago(dt):
    if dt is None:
        return ""
    if isinstance(dt, str):
        dt = parse_timestamp(dt)
        if dt is None:
            return ""
    delta = datetime.now(timezone.utc) - dt
    if delta.days == 0:
        h = delta.seconds // 3600
        if h == 0:
            return f"vor {delta.seconds // 60}m"
        return f"vor {h}h"
    if delta.days == 1:
        return "gestern"
    if delta.days < 7:
        return f"vor {delta.days}d"
    return dt.strftime("%d.%m.")


def session_title(s):
    """Echten Titel aus erster User-Message ableiten, nicht den Slug-Quatsch."""
    first = (s.get("first_user_message", "") or "").strip()
    # Skip plan/command prefixes
    for noise in ["Implement the following plan:", "<command-message>", "[Request interrupted"]:
        if first.startswith(noise):
            first = first[len(noise):].strip()
    # Skip markdown headers
    while first.startswith("#"):
        first = first.lstrip("#").strip()
    # Truncate
    if len(first) > 90:
        first = first[:87] + "..."
    return first or s.get("slug", "unnamed")


def msg_count(s):
    return (s.get("user_msg_count", 0) or 0) + (s.get("assistant_msg_count", 0) or 0)


# --- Load & Filter ---
all_sessions = load_sessions()
big_sessions = [s for s in all_sessions if msg_count(s) >= 10]


# --- Sidebar (hidden by default) ---
with st.sidebar:
    st.markdown("### Einstellungen")
    grid_count = st.slider("Anzahl Sessions", 4, 20, 10, step=2)
    min_msgs = st.slider("Min. Messages", 5, 50, 10)
    selected_projects = st.multiselect("Nur Projekte:", get_all_projects(), default=[])
    search_q = st.text_input("Suche", placeholder="Keyword...")

    if min_msgs != 10:
        big_sessions = [s for s in all_sessions if msg_count(s) >= min_msgs]
    if selected_projects:
        big_sessions = [s for s in big_sessions if s.get("project", "") in selected_projects]
    if search_q:
        q = search_q.lower()
        big_sessions = [
            s for s in big_sessions
            if q in (s.get("first_user_message", "") or "").lower()
            or q in (s.get("last_user_message", "") or "").lower()
            or q in (s.get("project", "") or "").lower()
        ]


display = big_sessions[:grid_count if 'grid_count' in dir() else 10]

# --- Cached full-text search ---
@st.cache_data(ttl=300, show_spinner="Durchsuche alle Sessions...")
def run_fulltext_search(keyword: str):
    return search_sessions(keyword)


# =============================================================
# HEADER + VOLLTEXTSUCHE
# =============================================================
st.markdown("## Wo war ich?")

# Prominent search bar in main area
search_col1, search_col2 = st.columns([4, 1])
with search_col1:
    fulltext_q = st.text_input(
        "Volltextsuche",
        placeholder="Alle Sessions durchsuchen (grep)...",
        label_visibility="collapsed",
    )
with search_col2:
    search_clicked = st.button("Suchen", type="primary", use_container_width=True)

# Determine if search is active
active_search = fulltext_q.strip() if (search_clicked or fulltext_q.strip()) else ""

if active_search:
    # =============================================================
    # SEARCH RESULTS VIEW — compact: 8-10 per screen
    # =============================================================
    results = run_fulltext_search(active_search)

    if not results:
        st.warning(f'Keine Treffer fuer "{active_search}"')
    else:
        st.caption(f'{len(results)} Sessions mit Treffern fuer "{active_search}"')

        for res in results:
            match_count = res.get("match_count", 0)
            slug = res.get("slug", "") or res["session_id"][:12]
            project = res.get("project", "")

            # Build resume command
            cwd = ""
            for s in all_sessions:
                if s["session_id"] == res["session_id"]:
                    cwd = s.get("cwd", "")
                    break
            resume_cmd = f"cd {cwd} && claude --resume {res['session_id']}" if cwd else f"claude --resume {res['session_id']}"

            # One-line header: slug — project · N Treffer · inline resume
            st.markdown(
                f"**{slug}** — {project} · {match_count} Treffer · `{resume_cmd}`"
            )

            # Filter empty matches, show max 1 snippet as plain text
            non_empty = [m for m in res.get("matches", []) if m.get("content", "").strip()]
            if non_empty:
                snippet = non_empty[0]["content"].strip()[:300]
                # Case-insensitive keyword highlight
                snippet = re.sub(
                    re.escape(active_search),
                    lambda m: f"**{m.group()}**",
                    snippet,
                    flags=re.IGNORECASE,
                )
                st.caption(snippet)

            # Everything else collapsed in expander
            with st.expander("Details + Conversation"):
                # Copyable resume command
                st.code(resume_cmd, language="bash")

                if match_count > 1 and len(non_empty) > 1:
                    st.markdown(f"**Alle {len(non_empty)} Snippets:**")
                    for match in non_empty[1:6]:
                        text = match["content"].strip()[:300]
                        text = re.sub(
                            re.escape(active_search),
                            lambda m: f"**{m.group()}**",
                            text,
                            flags=re.IGNORECASE,
                        )
                        st.markdown(f"- {text}")
                    if len(non_empty) > 6:
                        st.caption(f"... und {len(non_empty) - 6} weitere")

                # Conversation
                full = load_full_session(res["filepath"])
                if "error" in full:
                    st.error(full["error"])
                else:
                    mc1, mc2 = st.columns(2)
                    mc1.caption(f"${full.get('total_cost', 0):.2f} Kosten")
                    mc2.caption(f"{full.get('total_input_tokens',0)+full.get('total_output_tokens',0):,} Tokens")

                    messages = full.get("messages", [])
                    recent = messages[-10:]
                    for msg in recent:
                        role = msg.get("role", "")
                        text = msg.get("text", "")
                        if role == "user" and text and not text.startswith("[tool"):
                            with st.chat_message("user"):
                                st.markdown(text[:800])
                        elif role == "assistant" and text and not text.startswith("[tool:"):
                            with st.chat_message("assistant"):
                                st.markdown(text[:800])
                                model = msg.get("model", "")
                                if model:
                                    st.caption(model)

    st.divider()
    st.caption("Sidebar oeffnen fuer Filter · Expander fuer Details")
    st.stop()


# =============================================================
# DEFAULT VIEW — SESSION GRID
# =============================================================
st.caption(f"{len(big_sessions)} Sessions mit 10+ Messages · {len(all_sessions)} total")

if not display:
    st.info("Keine grossen Sessions gefunden.")
    st.stop()

for row_idx in range(0, len(display), 2):
    cols = st.columns(2, gap="medium")

    for col_idx in range(2):
        idx = row_idx + col_idx
        if idx >= len(display):
            break

        s = display[idx]
        title = session_title(s)
        project = s.get("project", "") or ""
        when = time_ago(s.get("last_timestamp"))
        msgs = msg_count(s)
        size = s.get("file_size_human", "")
        last_msg = (s.get("last_user_message", "") or "").strip()
        session_id = s["session_id"]
        cwd = s.get("cwd", "")

        # Clean up last_msg too
        for noise in ["Implement the following plan:", "<command-message>", "[Request interrupted"]:
            if last_msg.startswith(noise):
                last_msg = last_msg[len(noise):].strip()
        while last_msg.startswith("#"):
            last_msg = last_msg.lstrip("#").strip()
        if len(last_msg) > 120:
            last_msg = last_msg[:117] + "..."

        with cols[col_idx]:
            with st.container(border=True):
                # Title + metadata
                st.markdown(f"**{title}**")
                st.caption(f"{project} \u00b7 {when} \u00b7 {msgs} msgs \u00b7 {size}")

                # Where I stopped
                if last_msg and last_msg != title:
                    st.markdown(f"*Zuletzt:* {last_msg}")

                # Resume
                st.code(f"cd {cwd} && claude --resume {session_id}", language="bash")

                # Expandable details
                with st.expander("Conversation"):
                    full = load_full_session(s["filepath"])
                    if "error" in full:
                        st.error(full["error"])
                    else:
                        # Quick metrics
                        mc1, mc2 = st.columns(2)
                        mc1.caption(f"${full.get('total_cost', 0):.2f} Kosten")
                        mc2.caption(f"{full.get('total_input_tokens',0)+full.get('total_output_tokens',0):,} Tokens")

                        # Last 10 messages
                        messages = full.get("messages", [])
                        recent = messages[-10:]
                        for msg in recent:
                            role = msg.get("role", "")
                            text = msg.get("text", "")
                            if role == "user" and text and not text.startswith("[tool"):
                                with st.chat_message("user"):
                                    st.markdown(text[:800])
                            elif role == "assistant" and text and not text.startswith("[tool:"):
                                with st.chat_message("assistant"):
                                    st.markdown(text[:800])
                                    model = msg.get("model", "")
                                    if model:
                                        st.caption(model)


# =============================================================
# FOOTER
# =============================================================
st.divider()
st.caption("Sidebar oeffnen fuer Filter \u00b7 Expander fuer Conversation Details")
