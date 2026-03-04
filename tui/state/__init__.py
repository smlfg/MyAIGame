"""TUI state persistence — SQLite-backed session and cost tracking."""

from .models import (
    Session,
    Message,
    SkillInvocation,
    FocusSession,
    ParkedDistraction,
    Checkpoint,
    CostEvent,
)
from .repository import (
    SessionRepo,
    MessageRepo,
    CostRepo,
    FocusRepo,
    DistractionRepo,
)
from .database import init_db, get_db, close_db

# Convenience alias used by the team lead spec
StateManager = SessionRepo

__all__ = [
    # Models
    "Session",
    "Message",
    "SkillInvocation",
    "FocusSession",
    "ParkedDistraction",
    "Checkpoint",
    "CostEvent",
    # Repos
    "StateManager",
    "SessionRepo",
    "MessageRepo",
    "CostRepo",
    "FocusRepo",
    "DistractionRepo",
    # DB helpers
    "init_db",
    "get_db",
    "close_db",
]
