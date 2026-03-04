"""Pomodoro timer with state machine: IDLE → WORKING → BREAK → WORKING → ..."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Optional


class PomodoroState(Enum):
    IDLE = auto()
    WORKING = auto()
    BREAK = auto()
    PAUSED = auto()


@dataclass
class PomodoroStatus:
    state: PomodoroState
    goal: str
    remaining_seconds: int
    elapsed_sessions: int
    work_minutes: int
    break_minutes: int

    @property
    def remaining_display(self) -> str:
        m, s = divmod(self.remaining_seconds, 60)
        return f"{m:02d}:{s:02d}"

    @property
    def progress_fraction(self) -> float:
        if self.state == PomodoroState.WORKING:
            total = self.work_minutes * 60
        elif self.state == PomodoroState.BREAK:
            total = self.break_minutes * 60
        else:
            return 0.0
        if total == 0:
            return 0.0
        return max(0.0, 1.0 - self.remaining_seconds / total)


class PomodoroTimer:
    """
    State machine: IDLE -> WORKING -> BREAK -> WORKING -> ...

    Call tick() every second from an external scheduler (e.g. Textual's set_interval).
    Register on_work_complete and on_break_complete callbacks for UI reactions.
    """

    def __init__(self) -> None:
        self._state = PomodoroState.IDLE
        self._goal = ""
        self._work_minutes = 25
        self._break_minutes = 5
        self._remaining_seconds = 0
        self._elapsed_sessions = 0
        self._state_before_pause: Optional[PomodoroState] = None

        self.on_work_complete: Optional[Callable[["PomodoroTimer"], None]] = None
        self.on_break_complete: Optional[Callable[["PomodoroTimer"], None]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(
        self,
        goal: str,
        work_minutes: int = 25,
        break_minutes: int = 5,
    ) -> None:
        self._goal = goal
        self._work_minutes = work_minutes
        self._break_minutes = break_minutes
        self._elapsed_sessions = 0
        self._begin_work()

    def pause(self) -> None:
        if self._state in (PomodoroState.WORKING, PomodoroState.BREAK):
            self._state_before_pause = self._state
            self._state = PomodoroState.PAUSED

    def resume(self) -> None:
        if self._state == PomodoroState.PAUSED and self._state_before_pause is not None:
            self._state = self._state_before_pause
            self._state_before_pause = None

    def reset(self) -> None:
        self._state = PomodoroState.IDLE
        self._goal = ""
        self._remaining_seconds = 0
        self._elapsed_sessions = 0
        self._state_before_pause = None

    def tick(self) -> None:
        """Advance the timer by one second. Call this every second."""
        if self._state not in (PomodoroState.WORKING, PomodoroState.BREAK):
            return

        self._remaining_seconds -= 1

        if self._remaining_seconds <= 0:
            if self._state == PomodoroState.WORKING:
                self._elapsed_sessions += 1
                if self.on_work_complete:
                    self.on_work_complete(self)
                self._begin_break()
            else:  # BREAK
                if self.on_break_complete:
                    self.on_break_complete(self)
                self._begin_work()

    def get_status(self) -> PomodoroStatus:
        return PomodoroStatus(
            state=self._state,
            goal=self._goal,
            remaining_seconds=max(0, self._remaining_seconds),
            elapsed_sessions=self._elapsed_sessions,
            work_minutes=self._work_minutes,
            break_minutes=self._break_minutes,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _begin_work(self) -> None:
        self._state = PomodoroState.WORKING
        self._remaining_seconds = self._work_minutes * 60

    def _begin_break(self) -> None:
        self._state = PomodoroState.BREAK
        self._remaining_seconds = self._break_minutes * 60
