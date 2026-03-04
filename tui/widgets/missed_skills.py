"""MissedSkillsWidget — shows missed skill suggestions."""
from textual.widgets import Static


try:
    from tui.data.skill_tracker import get_missed_today
except ImportError:
    def get_missed_today():
        return []


class MissedSkillsWidget(Static):
    """Shows skills that were suggested but not used."""

    DEFAULT_CSS = """
    MissedSkillsWidget {
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
        try:
            raw = get_missed_today()
        except Exception:
            raw = []
        # Aggregate by suggested_skill
        counts: dict[str, int] = {}
        for entry in raw:
            skill = entry.get("suggested_skill", "unknown")
            counts[skill] = counts.get(skill, 0) + 1
        missed = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        lines = ["[bold]Missed Skills[/bold]"]
        if not missed:
            lines.append("[dim]None missed today[/dim]")
        else:
            for skill, count in missed[:5]:
                lines.append(
                    f"[#f85149]{skill}[/#f85149] [dim]({count}x missed)[/dim]"
                )

        self.update("\n".join(lines))
