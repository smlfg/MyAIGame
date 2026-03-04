"""ADHS Session Manager — orchestrates Pomodoro, Streaks, Parking Lot, and Quick Wins."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional

from .pomodoro import PomodoroTimer, PomodoroState, PomodoroStatus
from .streaks import StreakTracker, DayStats
from .parking import DistractionParkingLot, ParkedThought
from .quickwins import QuickWinGenerator, QuickWin


EnergyLevel = Literal["high", "medium", "low"]

# Energy level -> (work_minutes, break_minutes, quick_win_count)
_ENERGY_CONFIG: dict[EnergyLevel, tuple[int, int, int]] = {
    "high": (25, 5, 2),
    "medium": (15, 5, 3),
    "low": (10, 3, 3),
}


@dataclass
class SessionSummary:
    goal: str
    energy_level: EnergyLevel
    elapsed_sessions: int
    today_stats: DayStats
    parked_count: int
    quick_wins_available: list[QuickWin] = field(default_factory=list)


class ADHSSessionManager:
    """
    Central orchestrator for an ADHS-optimised work session.

    Usage:
        manager = ADHSSessionManager(session_id="abc-123", project_path=Path("."))
        manager.start_session("Finish skill_runner.py", energy_level="medium")
        # every second:
        manager.tick()
        # on distraction:
        manager.on_distraction("What's the best TUI framework?")
        # at pomodoro end or commit:
        manager.on_checkpoint()
    """

    def __init__(
        self,
        session_id: str,
        project_path: Optional[Path] = None,
    ) -> None:
        self._session_id = session_id
        self._project_path = project_path or Path(".")
        self._goal = ""
        self._energy_level: EnergyLevel = "medium"

        self.timer = PomodoroTimer()
        self.streaks = StreakTracker(session_id)
        self.parking = DistractionParkingLot(session_id)
        self._qw_generator = QuickWinGenerator()
        self._quick_wins: list[QuickWin] = []

        # Callbacks for the TUI layer
        self.on_work_complete_cb: Optional[Callable[[PomodoroStatus], None]] = None
        self.on_break_complete_cb: Optional[Callable[[PomodoroStatus], None]] = None
        self.on_checkpoint_cb: Optional[Callable[[SessionSummary], None]] = None

        # Wire up pomodoro callbacks
        self.timer.on_work_complete = self._handle_work_complete
        self.timer.on_break_complete = self._handle_break_complete

        # Track sessions recorded so we don't double-record
        self._last_recorded_sessions = 0

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_session(self, goal: str, energy_level: EnergyLevel = "medium") -> list[QuickWin]:
        """
        Start a new ADHS session.

        Returns a list of quick wins appropriate for the energy level — ready
        to display on the startup screen without extra work from the TUI.
        """
        self._goal = goal
        self._energy_level = energy_level
        work_min, break_min, qw_count = _ENERGY_CONFIG[energy_level]

        self.timer.start(goal=goal, work_minutes=work_min, break_minutes=break_min)

        self._quick_wins = self._qw_generator.generate(self._project_path, count=qw_count)
        return self._quick_wins

    def end_session(self) -> SessionSummary:
        """Stop timer and return a final summary."""
        status = self.timer.get_status()
        if status.state in (PomodoroState.WORKING, PomodoroState.BREAK):
            self._record_current_pomodoro(completed=False)
        self.timer.reset()
        return self._build_summary()

    # ------------------------------------------------------------------
    # Per-tick update
    # ------------------------------------------------------------------

    def tick(self) -> None:
        """Advance the timer by one second. Call from Textual set_interval(1)."""
        self.timer.tick()

    # ------------------------------------------------------------------
    # Distraction handling
    # ------------------------------------------------------------------

    def on_distraction(self, thought: str) -> ParkedThought:
        """Auto-park a distraction so focus is preserved."""
        return self.parking.park(thought)

    # ------------------------------------------------------------------
    # Checkpoint (manual trigger or git hook)
    # ------------------------------------------------------------------

    def on_checkpoint(self) -> SessionSummary:
        """Celebrate progress, update streak, refresh quick wins."""
        self._record_current_pomodoro(completed=True)
        self._quick_wins = self._qw_generator.generate(
            self._project_path,
            count=_ENERGY_CONFIG[self._energy_level][2],
        )
        summary = self._build_summary()
        if self.on_checkpoint_cb:
            self.on_checkpoint_cb(summary)
        return summary

    def refresh_quick_wins(self) -> list[QuickWin]:
        """Refresh quick wins list — called from 'Refresh' button."""
        count = _ENERGY_CONFIG[self._energy_level][2]
        self._quick_wins = self._qw_generator.generate(self._project_path, count=count)
        return self._quick_wins

    # ------------------------------------------------------------------
    # Status / summary
    # ------------------------------------------------------------------

    def get_pomodoro_status(self) -> PomodoroStatus:
        return self.timer.get_status()

    def get_summary(self) -> SessionSummary:
        return self._build_summary()

    def get_quick_wins(self) -> list[QuickWin]:
        return list(self._quick_wins)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_work_complete(self, timer: PomodoroTimer) -> None:
        self._record_current_pomodoro(completed=True)
        status = timer.get_status()
        if self.on_work_complete_cb:
            self.on_work_complete_cb(status)

    def _handle_break_complete(self, timer: PomodoroTimer) -> None:
        status = timer.get_status()
        if self.on_break_complete_cb:
            self.on_break_complete_cb(status)

    def _record_current_pomodoro(self, completed: bool) -> None:
        status = self.timer.get_status()
        # Only record if we've actually advanced past the last recorded session
        if status.elapsed_sessions <= self._last_recorded_sessions and completed:
            return
        work_min = status.work_minutes
        self.streaks.record_focus_session(
            goal=self._goal,
            planned_minutes=work_min,
            actual_minutes=work_min if completed else max(1, work_min - status.remaining_seconds // 60),
            completed=completed,
        )
        if completed:
            self._last_recorded_sessions = status.elapsed_sessions

    def _build_summary(self) -> SessionSummary:
        status = self.timer.get_status()
        return SessionSummary(
            goal=self._goal,
            energy_level=self._energy_level,
            elapsed_sessions=status.elapsed_sessions,
            today_stats=self.streaks.get_today_stats(),
            parked_count=self.parking.count(),
            quick_wins_available=list(self._quick_wins),
        )
