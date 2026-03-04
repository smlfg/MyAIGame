"""Distraction Parking Lot — park thoughts, promote to tasks, or dismiss."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..state import DistractionRepo, ParkedDistraction


@dataclass
class ParkedThought:
    id: str
    text: str
    created_at: datetime
    category: str  # Lernen / Recherche / Feature / Housekeeping / Sonstiges

    @classmethod
    def from_state(cls, d: ParkedDistraction) -> "ParkedThought":
        return cls(
            id=d.id,
            text=d.text,
            created_at=d.created_at,
            category=_categorize(d.text),
        )


_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Lernen", ["tutorial", "lesen", "lernen", "kurs", "buch", "anleitung", "erkunden", "verstehen"]),
    ("Recherche", ["recherche", "suchen", "vergleich", "was ist", "wie baut", "wie funktioniert", "finden"]),
    ("Feature", ["feature", "funktion", "implementieren", "bauen", "hinzufuegen", "refactor"]),
    ("Housekeeping", ["readme", "gitignore", "aufraumen", "cleanup", "rename", "format", "lint", "doc", "kommentar"]),
]


def _categorize(text: str) -> str:
    lower = text.lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return category
    return "Sonstiges"


class DistractionParkingLot:
    """
    Thread-safe parking lot backed by DistractionRepo (SQLite).

    The session_id ties parked thoughts to the current TUI session so they
    can be exported at session-end.
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def park(self, thought: str) -> ParkedThought:
        """Save a distraction for later — one keypress, no rabbit hole."""
        d = DistractionRepo.park(self._session_id, thought)
        return ParkedThought.from_state(d)

    def promote(self, thought_id: str) -> None:
        """Convert a parked thought to an actionable task / skill invocation."""
        DistractionRepo.promote(thought_id)

    def dismiss(self, thought_id: str) -> None:
        """Remove a thought without acting on it."""
        from ..state.database import get_db
        with get_db() as conn:
            conn.execute(
                "DELETE FROM parked_distractions WHERE id = ?",
                (thought_id,),
            )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list_parked(self) -> list[ParkedThought]:
        """Return all non-promoted parked thoughts for the current session."""
        distractions = DistractionRepo.list_parked(self._session_id)
        return [ParkedThought.from_state(d) for d in distractions]

    def count(self) -> int:
        return len(self.list_parked())
