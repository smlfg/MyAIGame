"""Repository pattern for all TUI state entities."""

import uuid
from datetime import datetime, date
from typing import Optional

from .database import get_db
from .models import (
    Session, Message, SkillInvocation, FocusSession,
    ParkedDistraction, Checkpoint, CostEvent,
)


def _now() -> str:
    return datetime.utcnow().isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if s is None:
        return None
    return datetime.fromisoformat(s)


# ---------------------------------------------------------------------------
# SessionRepo
# ---------------------------------------------------------------------------

class SessionRepo:
    @staticmethod
    def create(goal: str, provider: str = "") -> Session:
        sess = Session(
            id=_new_id(),
            goal=goal,
            started_at=datetime.utcnow(),
            ended_at=None,
            provider=provider,
            total_cost=0.0,
            status="active",
        )
        with get_db() as conn:
            conn.execute(
                """INSERT INTO sessions (id, goal, started_at, ended_at, provider, total_cost, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sess.id, sess.goal, sess.started_at.isoformat(),
                 None, sess.provider, sess.total_cost, sess.status),
            )
        return sess

    @staticmethod
    def get(session_id: str) -> Optional[Session]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        if row is None:
            return None
        return Session(
            id=row["id"], goal=row["goal"],
            started_at=datetime.fromisoformat(row["started_at"]),
            ended_at=_parse_dt(row["ended_at"]),
            provider=row["provider"], total_cost=row["total_cost"],
            status=row["status"],
        )

    @staticmethod
    def list(limit: int = 50) -> list[Session]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            Session(
                id=r["id"], goal=r["goal"],
                started_at=datetime.fromisoformat(r["started_at"]),
                ended_at=_parse_dt(r["ended_at"]),
                provider=r["provider"], total_cost=r["total_cost"],
                status=r["status"],
            )
            for r in rows
        ]

    @staticmethod
    def update(session_id: str, **kwargs) -> None:
        allowed = {"goal", "ended_at", "provider", "total_cost", "status"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        # Serialize datetime values
        for k, v in fields.items():
            if isinstance(v, datetime):
                fields[k] = v.isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [session_id]
        with get_db() as conn:
            conn.execute(
                f"UPDATE sessions SET {set_clause} WHERE id = ?", values
            )

    @staticmethod
    def delete(session_id: str) -> None:
        with get_db() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    @staticmethod
    def get_active() -> Optional[Session]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE status = 'active' ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return Session(
            id=row["id"], goal=row["goal"],
            started_at=datetime.fromisoformat(row["started_at"]),
            ended_at=_parse_dt(row["ended_at"]),
            provider=row["provider"], total_cost=row["total_cost"],
            status=row["status"],
        )


# ---------------------------------------------------------------------------
# MessageRepo
# ---------------------------------------------------------------------------

class MessageRepo:
    @staticmethod
    def add(session_id: str, role: str, content: str,
            tokens_in: int = 0, tokens_out: int = 0, cost: float = 0.0) -> Message:
        msg = Message(
            id=_new_id(), session_id=session_id, role=role, content=content,
            timestamp=datetime.utcnow(), tokens_in=tokens_in,
            tokens_out=tokens_out, cost=cost,
        )
        with get_db() as conn:
            conn.execute(
                """INSERT INTO messages (id, session_id, role, content, timestamp, tokens_in, tokens_out, cost)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (msg.id, msg.session_id, msg.role, msg.content,
                 msg.timestamp.isoformat(), msg.tokens_in, msg.tokens_out, msg.cost),
            )
        return msg

    @staticmethod
    def get_by_session(session_id: str) -> list[Message]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,),
            ).fetchall()
        return [
            Message(
                id=r["id"], session_id=r["session_id"], role=r["role"],
                content=r["content"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                tokens_in=r["tokens_in"], tokens_out=r["tokens_out"], cost=r["cost"],
            )
            for r in rows
        ]

    @staticmethod
    def get_recent(session_id: str, limit: int = 20) -> list[Message]:
        with get_db() as conn:
            rows = conn.execute(
                """SELECT * FROM messages WHERE session_id = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (session_id, limit),
            ).fetchall()
        messages = [
            Message(
                id=r["id"], session_id=r["session_id"], role=r["role"],
                content=r["content"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                tokens_in=r["tokens_in"], tokens_out=r["tokens_out"], cost=r["cost"],
            )
            for r in rows
        ]
        return list(reversed(messages))


# ---------------------------------------------------------------------------
# CostRepo
# ---------------------------------------------------------------------------

class CostRepo:
    @staticmethod
    def add_event(session_id: str, provider: str, model: str,
                  tokens_in: int, tokens_out: int, cost: float,
                  context: str = "message") -> CostEvent:
        event = CostEvent(
            id=_new_id(), session_id=session_id, provider=provider, model=model,
            tokens_in=tokens_in, tokens_out=tokens_out, cost=cost,
            timestamp=datetime.utcnow(), context=context,
        )
        with get_db() as conn:
            conn.execute(
                """INSERT INTO cost_events
                   (id, session_id, provider, model, tokens_in, tokens_out, cost, timestamp, context)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (event.id, event.session_id, event.provider, event.model,
                 event.tokens_in, event.tokens_out, event.cost,
                 event.timestamp.isoformat(), event.context),
            )
            # Update session total_cost
            conn.execute(
                "UPDATE sessions SET total_cost = total_cost + ? WHERE id = ?",
                (cost, session_id),
            )
        return event

    @staticmethod
    def get_session_cost(session_id: str) -> float:
        with get_db() as conn:
            row = conn.execute(
                "SELECT SUM(cost) as total FROM cost_events WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return row["total"] or 0.0

    @staticmethod
    def get_daily_cost(day: Optional[date] = None) -> float:
        target = (day or date.today()).isoformat()
        with get_db() as conn:
            row = conn.execute(
                "SELECT SUM(cost) as total FROM cost_events WHERE date(timestamp) = ?",
                (target,),
            ).fetchone()
        return row["total"] or 0.0

    @staticmethod
    def get_monthly_cost(year: int, month: int) -> float:
        prefix = f"{year:04d}-{month:02d}"
        with get_db() as conn:
            row = conn.execute(
                "SELECT SUM(cost) as total FROM cost_events WHERE strftime('%Y-%m', timestamp) = ?",
                (prefix,),
            ).fetchone()
        return row["total"] or 0.0


# ---------------------------------------------------------------------------
# FocusRepo
# ---------------------------------------------------------------------------

class FocusRepo:
    @staticmethod
    def start(session_id: str, goal: str, duration_planned: int) -> FocusSession:
        fs = FocusSession(
            id=_new_id(), session_id=session_id, goal=goal,
            started_at=datetime.utcnow(), duration_planned=duration_planned,
            duration_actual=None, completed=False,
        )
        with get_db() as conn:
            conn.execute(
                """INSERT INTO focus_sessions
                   (id, session_id, goal, started_at, duration_planned, duration_actual, completed)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (fs.id, fs.session_id, fs.goal, fs.started_at.isoformat(),
                 fs.duration_planned, None, 0),
            )
        return fs

    @staticmethod
    def complete(focus_id: str, duration_actual: int) -> None:
        with get_db() as conn:
            conn.execute(
                "UPDATE focus_sessions SET completed = 1, duration_actual = ? WHERE id = ?",
                (duration_actual, focus_id),
            )

    @staticmethod
    def get_streak() -> int:
        """Number of consecutive days with at least one completed focus session."""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT DISTINCT date(started_at) as day
                   FROM focus_sessions WHERE completed = 1
                   ORDER BY day DESC"""
            ).fetchall()
        if not rows:
            return 0
        streak = 0
        expected = date.today()
        for row in rows:
            day = date.fromisoformat(row["day"])
            if day == expected:
                streak += 1
                from datetime import timedelta
                expected = expected - timedelta(days=1)
            else:
                break
        return streak

    @staticmethod
    def get_history(limit: int = 30) -> list[FocusSession]:
        with get_db() as conn:
            rows = conn.execute(
                """SELECT * FROM focus_sessions ORDER BY started_at DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            FocusSession(
                id=r["id"], session_id=r["session_id"], goal=r["goal"],
                started_at=datetime.fromisoformat(r["started_at"]),
                duration_planned=r["duration_planned"],
                duration_actual=r["duration_actual"],
                completed=bool(r["completed"]),
            )
            for r in rows
        ]


# ---------------------------------------------------------------------------
# DistractionRepo
# ---------------------------------------------------------------------------

class DistractionRepo:
    @staticmethod
    def park(session_id: str, text: str) -> ParkedDistraction:
        d = ParkedDistraction(
            id=_new_id(), session_id=session_id, text=text,
            created_at=datetime.utcnow(), promoted_to_task=False,
        )
        with get_db() as conn:
            conn.execute(
                """INSERT INTO parked_distractions
                   (id, session_id, text, created_at, promoted_to_task)
                   VALUES (?, ?, ?, ?, ?)""",
                (d.id, d.session_id, d.text, d.created_at.isoformat(), 0),
            )
        return d

    @staticmethod
    def promote(distraction_id: str) -> None:
        with get_db() as conn:
            conn.execute(
                "UPDATE parked_distractions SET promoted_to_task = 1 WHERE id = ?",
                (distraction_id,),
            )

    @staticmethod
    def list_parked(session_id: str) -> list[ParkedDistraction]:
        with get_db() as conn:
            rows = conn.execute(
                """SELECT * FROM parked_distractions
                   WHERE session_id = ? AND promoted_to_task = 0
                   ORDER BY created_at ASC""",
                (session_id,),
            ).fetchall()
        return [
            ParkedDistraction(
                id=r["id"], session_id=r["session_id"], text=r["text"],
                created_at=datetime.fromisoformat(r["created_at"]),
                promoted_to_task=bool(r["promoted_to_task"]),
            )
            for r in rows
        ]
