"""ServicesTLDRWidget — service status + today's TLDR."""
import urllib.request
import urllib.error
from textual.widgets import Static


DAEMON_PORT = 7742
VOICE_PORT = 5050


def _ping(port: int) -> bool:
    """Return True if port responds within 2s."""
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=2)
        return req.status < 500
    except Exception:
        return False


def _dot(online: bool) -> str:
    if online:
        return "[bold #3fb950]●[/bold #3fb950]"
    return "[bold #f85149]●[/bold #f85149]"


try:
    from tui.data.usage_reader import get_daily_summary
except ImportError:
    def get_daily_summary():
        return {"total_calls": 0, "unique_tools": 0, "cost_estimate_usd": 0.0}


class ServicesTLDRWidget(Static):
    """Shows service health + daily TLDR stats."""

    DEFAULT_CSS = """
    ServicesTLDRWidget {
        background: #161b22;
        color: #e6edf3;
        border: solid #30363d;
        height: auto;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        self._refresh()
        self.set_interval(15, self._refresh)

    def _refresh(self) -> None:
        self.run_worker(self._async_refresh, exclusive=True)

    async def _async_refresh(self) -> None:
        import asyncio
        daemon_ok = await asyncio.to_thread(_ping, DAEMON_PORT)
        voice_ok = await asyncio.to_thread(_ping, VOICE_PORT)

        try:
            summary = get_daily_summary()
        except Exception:
            summary = {"total_calls": 0, "unique_tools": 0, "cost_estimate_usd": 0.0}

        total_calls = summary.get("total_calls", 0)
        unique_tools = summary.get("unique_tools", 0)
        cost = summary.get("cost_estimate_usd", 0.0)

        lines = [
            "[bold]Services + TLDR[/bold]",
            f"{_dot(daemon_ok)} Daemon :{DAEMON_PORT}   {_dot(voice_ok)} Voice :{VOICE_PORT}",
            "─" * 28,
            f"Calls: [#58a6ff]{total_calls}[/#58a6ff]  "
            f"Unique Tools: [#58a6ff]{unique_tools}[/#58a6ff]  "
            f"Cost: [#3fb950]${cost:.3f}[/#3fb950]",
        ]

        self.update("\n".join(lines))
