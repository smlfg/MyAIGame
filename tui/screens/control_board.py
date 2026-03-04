"""Control Board screen — 2x3 grid of monitoring widgets."""

from __future__ import annotations

from textual.screen import Screen
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Container
from textual.widgets import Static, Footer

from tui.widgets.tool_usage import ToolUsageWidget
from tui.widgets.voice_control import VoiceControlWidget
from tui.widgets.learn_tips import LearnTipsWidget
from tui.widgets.missed_skills import MissedSkillsWidget
from tui.widgets.session_grid import SessionGridWidget
from tui.widgets.services_tldr import ServicesTLDRWidget


CONTROL_BOARD_CSS = """
ControlBoardScreen {
    align: center middle;
    background: #0d1117;
}

#cb-title {
    height: 3;
    width: 100%;
    background: #161b22;
    border-bottom: solid #30363d;
    color: #58a6ff;
    content-align: center middle;
    text-style: bold;
}

#control-grid {
    grid-size: 2 3;
    grid-gutter: 1;
    width: 80;
    height: 30;
    padding: 1;
    background: #0d1117;
    border: solid #30363d;
}

.tile {
    background: #161b22;
    border: solid #30363d;
    padding: 1;
    height: 100%;
}

#cb-footer {
    height: 1;
    width: 100%;
    background: #21262d;
    color: #484f58;
    content-align: center middle;
}
"""


class ControlBoardScreen(Screen):
    """Control Board — 2x3 grid monitoring screen."""

    CSS = CONTROL_BOARD_CSS

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("tab", "focus_next", "Next Tile", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Control Board", id="cb-title")
        yield Grid(
            Container(ToolUsageWidget(), classes="tile"),
            Container(VoiceControlWidget(), classes="tile"),
            Container(LearnTipsWidget(), classes="tile"),
            Container(MissedSkillsWidget(), classes="tile"),
            Container(SessionGridWidget(), classes="tile"),
            Container(ServicesTLDRWidget(), classes="tile"),
            id="control-grid",
        )
        yield Static(
            "Ctrl+B = Toggle | Tab = Next | Enter = Action | Esc = Close",
            id="cb-footer",
        )
