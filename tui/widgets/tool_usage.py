"""ToolUsageWidget — shows top 5 tools today as compact bars."""
from textual.widgets import Static


try:
    from tui.data.usage_reader import get_top_n
except ImportError:
    def get_top_n(n: int = 5):
        return []


BAR_CHARS = "█"
MAX_BAR_WIDTH = 10


def _render_bar(count: int, max_count: int) -> str:
    if max_count == 0:
        return ""
    width = round((count / max_count) * MAX_BAR_WIDTH)
    return BAR_CHARS * width


class ToolUsageWidget(Static):
    """Shows top 5 tools used today as compact bars."""

    DEFAULT_CSS = """
    ToolUsageWidget {
        background: #161b22;
        color: #e6edf3;
        border: solid #30363d;
        height: auto;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        self._refresh_data()
        self.set_interval(30, self._refresh_data)

    def _refresh_data(self) -> None:
        try:
            data = get_top_n(5)
        except Exception:
            data = []

        if not data:
            self.update("[dim]No tool data[/dim]")
            return

        max_count = max(count for _, count in data) if data else 1
        lines = ["[bold]Top 5 Today[/bold]"]
        for tool, count in data:
            bar = _render_bar(count, max_count)
            short_name = tool[:20] if len(tool) > 20 else tool
            lines.append(f"[#58a6ff]{short_name:<20}[/#58a6ff] [#3fb950]{bar}[/#3fb950] {count}")

        self.update("\n".join(lines))
