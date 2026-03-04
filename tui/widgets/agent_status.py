"""AgentStatus — shows active provider/agent."""
from textual.widgets import Static


class AgentStatus(Static):
    """Displays the currently active AI provider."""

    DEFAULT_CSS = """
    AgentStatus {
        background: #161b22;
        color: #e6edf3;
        border: solid #30363d;
        height: 3;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__("Agent: [dim]idle[/dim]", **kwargs)
        self._provider: str = ""

    def set_active_provider(self, name: str) -> None:
        """Update the displayed active provider."""
        self._provider = name
        if name:
            self.update(f"Agent: [bold #58a6ff]{name}[/bold #58a6ff]")
        else:
            self.update("Agent: [dim]idle[/dim]")
