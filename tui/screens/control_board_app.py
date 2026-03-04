"""Standalone entrypoint for the Control Board screen."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding

from tui.screens.control_board import ControlBoardScreen


class ControlBoardApp(App):
    """Standalone app that launches just the Control Board."""

    BINDINGS = [
        Binding("ctrl+b", "quit", "Close"),
        Binding("escape", "quit", "Close"),
    ]

    def on_mount(self) -> None:
        self.push_screen(ControlBoardScreen())


if __name__ == "__main__":
    ControlBoardApp().run()
