"""Streak tracker — records focus sessions and computes consecutive-day streaks."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from ..state import FocusRepo, DistractionRepo


@dataclass
class DayStats:
    sessions: int
    total_minutes: int
    streak: int


class StreakTracker:
    """
    Wraps the state-layer FocusRepo to expose streak and daily stats.

    All persistence is delegated to the existing SQLite-backed FocusRepo so
    there is exactly one source of truth.
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def record_focus_session(
        self,
        goal: str,
        planned_minutes: int,
        actual_minutes: int,
        completed: bool,
    ) -> None:
        """Persist a completed (or abandoned) focus session."""
        fs = FocusRepo.start(self._session_id, goal, planned_minutes)
        if completed or actual_minutes > 0:
            FocusRepo.complete(fs.id, actual_minutes)
            if not completed:
                # Mark incomplete by setting completed=False via direct update
                # FocusRepo.complete always sets completed=1; we need an extra step
                # for abandoned sessions — write the actual_minutes but keep
                # completed flag false.  For now we treat partial as not complete.
                from ..state.database import get_db
                with get_db() as conn:
                    conn.execute(
                        "UPDATE focus_sessions SET completed = 0 WHERE id = ?",
                        (fs.id,),
                    )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_current_streak(self) -> int:
        """Consecutive days (ending today) with at least one completed session."""
        return FocusRepo.get_streak()

    def get_best_streak(self) -> int:
        """Longest consecutive-day streak in recorded history."""
        history = FocusRepo.get_history(limit=365)
        if not history:
            return 0

        completed_days = sorted(
            {fs.started_at.date() for fs in history if fs.completed},
            reverse=True,
        )
        if not completed_days:
            return 0

        best = 1
        current = 1
        for i in range(1, len(completed_days)):
            if completed_days[i - 1] - completed_days[i] == timedelta(days=1):
                current += 1
                best = max(best, current)
            else:
                current = 1
        return best

    def get_today_stats(self) -> DayStats:
        """Sessions + total focused minutes for today."""
        history = FocusRepo.get_history(limit=100)
        today = date.today()
        today_sessions = [
            fs for fs in history
            if fs.started_at.date() == today and fs.completed
        ]
        total_minutes = sum(
            fs.duration_actual or 0 for fs in today_sessions
        )
        return DayStats(
            sessions=len(today_sessions),
            total_minutes=total_minutes,
            streak=self.get_current_streak(),
        )
