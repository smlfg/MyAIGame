"""FocusBar — shows current focus goal."""
from textual.widgets import Static


class FocusBar(Static):
    """Displays the current focus/goal for the session."""

    DEFAULT_CSS = """
    FocusBar {
        background: #161b22;
        color: #e6edf3;
        border: solid #30363d;
        height: 3;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__("Focus: [dim]No goal set[/dim]", **kwargs)
        self._goal: str = ""

    def prompt_new_goal(self, goal: str = "") -> None:
        """Set a new focus goal."""
        self._goal = goal
        if goal:
            self.update(f"Focus: [bold #58a6ff]{goal}[/bold #58a6ff]")
        else:
            self.update("Focus: [dim]No goal set[/dim]")
