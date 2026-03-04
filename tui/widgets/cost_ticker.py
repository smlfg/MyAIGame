"""CostTicker — shows running cost."""
from textual.widgets import Static


class CostTicker(Static):
    """Displays the running cost for the current session."""

    DEFAULT_CSS = """
    CostTicker {
        background: #161b22;
        color: #e6edf3;
        border: solid #30363d;
        height: 3;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__("Cost: [bold #3fb950]$0.0000[/bold #3fb950]", **kwargs)
        self._total: float = 0.0

    def add_cost(self, amount: float) -> None:
        """Add cost amount and update display."""
        self._total += amount
        color = "#f85149" if self._total > 1.0 else "#3fb950"
        self.update(f"Cost: [bold {color}]${self._total:.4f}[/bold {color}]")
