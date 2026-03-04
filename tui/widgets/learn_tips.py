"""LearnTipsWidget — shows a random tip."""
import random
from textual.widgets import Static


FALLBACK_TIPS = [
    "Use /recap before starting a new session.",
    "Delegate research to Gemini, not Opus SubAgents.",
    "CLI first — if no LLM needed, use shell.",
    "Waves, not explosions — one agent at a time.",
    "Test after every build, not just at the end.",
    "Specific git add, never git add -A blindly.",
    "Read before you modify — always.",
    "/learn after every session, not just /recap.",
    "Context beats convention — read the codebase first.",
    "One session with understanding > 10 sessions with output.",
]


try:
    from tui.data.tips_db import get_random_tip
except ImportError:
    def get_random_tip() -> str:
        return random.choice(FALLBACK_TIPS)


class LearnTipsWidget(Static):
    """Shows a random learning tip. Press Enter for a new one."""

    DEFAULT_CSS = """
    LearnTipsWidget {
        background: #161b22;
        color: #e6edf3;
        border: solid #30363d;
        height: auto;
        padding: 0 1;
    }
    """

    def on_mount(self) -> None:
        self._show_tip()

    def _show_tip(self) -> None:
        try:
            tip = get_random_tip()
        except Exception:
            tip = random.choice(FALLBACK_TIPS)
        self.update(f"[bold]Tipp[/bold]\n[#58a6ff]{tip}[/#58a6ff]\n[dim]↵ for new tip[/dim]")

    def on_key(self, event) -> None:
        if event.key == "enter":
            self._show_tip()
