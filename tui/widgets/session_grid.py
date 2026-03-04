"""SessionGridWidget — shows recent sessions."""
import sys
from pathlib import Path
from datetime import datetime, timezone
from textual.widgets import Static

# Add session-browser to path once at module level
_sb_path = str(Path.home() / "Projekte/MyAIGame/session-browser")
if _sb_path not in sys.path:
    sys.path.insert(0, _sb_path)


def _load_sessions():
    """Try to load sessions from session_parser, fallback to empty list."""
    try:
        from session_parser import quick_parse_all  # noqa: PLC0415
        sessions = quick_parse_all()
        return sessions[:5] if sessions else []
    except Exception:
        return None


def _format_age(dt) -> str:
    """Format datetime as human-readable age."""
    try:
        now = datetime.now(timezone.utc)
        if hasattr(dt, 'tzinfo') and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = now - dt
        minutes = int(delta.total_seconds() / 60)
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        return f"{hours // 24}d ago"
    except Exception:
        return "?"


class SessionGridWidget(Static):
    """Shows 5 most recent Claude sessions."""

    DEFAULT_CSS = """
    SessionGridWidget {
        background: #161b22;
        color: #e6edf3;
        border: solid #30363d;
        height: auto;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        self._refresh_data()
        self.set_interval(60, self._refresh_data)

    def _refresh_data(self) -> None:
        sessions = _load_sessions()

        lines = ["[bold]Sessions[/bold]"]

        if sessions is None:
            lines.append("[dim]Session Browser unavailable[/dim]")
        elif not sessions:
            lines.append("[dim]No sessions found[/dim]")
        else:
            for session in sessions:
                try:
                    title = getattr(session, 'title', None) or getattr(session, 'id', 'Unknown')
                    title = str(title)[:30]
                    dt = getattr(session, 'updated_at', None) or getattr(session, 'created_at', None)
                    age = _format_age(dt) if dt else "?"
                    lines.append(f"[#58a6ff]{title:<30}[/#58a6ff] [dim]{age}[/dim]")
                except Exception:
                    lines.append("[dim]Session parse error[/dim]")

        self.update("\n".join(lines))
