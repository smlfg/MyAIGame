import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="MAS Dashboard", layout="wide", page_icon="🤖")

from data.loader import load_events, get_session_list, get_active_events
from components.shared import session_picker, auto_refresh_toggle, agent_color_map

if "events" not in st.session_state:
    st.session_state.events = []

if "page" not in st.session_state:
    st.session_state.page = "War Room"

st.session_state.page = st.sidebar.radio(
    "View",
    ["War Room", "Timeline", "Cost Analysis", "Storyboard"],
    index=["War Room", "Timeline", "Cost Analysis", "Storyboard"].index(
        st.session_state.page
    ),
)

sessions = get_session_list()
claude_sess, opencode_sess = session_picker(sessions)

auto_refresh, interval = auto_refresh_toggle()

if auto_refresh:
    st_autorefresh(interval=interval * 1000, key="refresh")

events = load_events(claude_session=claude_sess, opencode_session=opencode_sess)
st.session_state.events = events

if st.session_state.page == "War Room":
    from views.warroom import render
elif st.session_state.page == "Timeline":
    from views.timeline import render
elif st.session_state.page == "Cost Analysis":
    from views.sankey_costs import render
elif st.session_state.page == "Storyboard":
    from views.storyboard import render

render()
