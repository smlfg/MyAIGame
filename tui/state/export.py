"""Export functions for sessions, costs, and focus statistics."""

import csv
import io
from datetime import date, datetime
from typing import Optional

from .database import get_db
from .repository import SessionRepo, MessageRepo, CostRepo, FocusRepo, DistractionRepo


def export_session_markdown(session_id: str) -> str:
    """Export a full session as SESSION_LOG.md formatted string."""
    session = SessionRepo.get(session_id)
    if session is None:
        raise ValueError(f"Session {session_id} not found")

    messages = MessageRepo.get_by_session(session_id)
    distractions = DistractionRepo.list_parked(session_id)

    with get_db() as conn:
        checkpoints = conn.execute(
            "SELECT * FROM checkpoints WHERE session_id = ? ORDER BY rowid ASC",
            (session_id,),
        ).fetchall()

    lines: list[str] = []

    # Header
    lines.append(f"# Session Log — {session.goal}")
    lines.append("")
    lines.append(f"- **ID:** `{session.id}`")
    lines.append(f"- **Provider:** {session.provider or 'unknown'}")
    lines.append(f"- **Started:** {session.started_at.strftime('%Y-%m-%d %H:%M UTC')}")
    if session.ended_at:
        lines.append(f"- **Ended:** {session.ended_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"- **Status:** {session.status}")
    lines.append(f"- **Total Cost:** ${session.total_cost:.4f}")
    lines.append("")

    # Conversation
    if messages:
        lines.append("## Conversation")
        lines.append("")
        for msg in messages:
            role_label = msg.role.capitalize()
            ts = msg.timestamp.strftime("%H:%M")
            lines.append(f"### {role_label} [{ts}]")
            lines.append("")
            lines.append(msg.content)
            if msg.tokens_in or msg.tokens_out:
                lines.append("")
                lines.append(
                    f"*Tokens: {msg.tokens_in} in / {msg.tokens_out} out"
                    f" | Cost: ${msg.cost:.4f}*"
                )
            lines.append("")

    # Checkpoints
    if checkpoints:
        lines.append("## Checkpoints")
        lines.append("")
        for cp in checkpoints:
            passed = (
                "PASS" if cp["tests_passed"] == 1
                else "FAIL" if cp["tests_passed"] == 0
                else "unknown"
            )
            lines.append(
                f"- `{cp['git_hash'][:8]}` — {cp['summary']}"
                f" ({cp['files_changed']} files, tests: {passed})"
            )
        lines.append("")

    # Parked distractions
    if distractions:
        lines.append("## Parked Distractions")
        lines.append("")
        for d in distractions:
            promoted = " *(promoted)*" if d.promoted_to_task else ""
            lines.append(f"- {d.text}{promoted}")
        lines.append("")

    return "\n".join(lines)


def export_costs_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> str:
    """Export cost events as CSV string for the given date range."""
    conditions = []
    params: list = []

    if start_date:
        conditions.append("date(timestamp) >= ?")
        params.append(start_date.isoformat())
    if end_date:
        conditions.append("date(timestamp) <= ?")
        params.append(end_date.isoformat())

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT ce.*, s.goal as session_goal
                FROM cost_events ce
                LEFT JOIN sessions s ON s.id = ce.session_id
                {where}
                ORDER BY ce.timestamp ASC""",
            params,
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp", "session_id", "session_goal", "provider", "model",
        "tokens_in", "tokens_out", "cost_usd", "context",
    ])
    for r in rows:
        writer.writerow([
            r["timestamp"], r["session_id"], r["session_goal"] or "",
            r["provider"], r["model"], r["tokens_in"], r["tokens_out"],
            f"{r['cost']:.6f}", r["context"],
        ])

    return output.getvalue()


def export_focus_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict:
    """Return focus statistics dict for the given date range.

    Keys:
        total_sessions, completed_sessions, completion_rate,
        total_planned_minutes, total_actual_minutes,
        average_completion_pct, streak, by_day (list of dicts)
    """
    conditions = []
    params: list = []

    if start_date:
        conditions.append("date(started_at) >= ?")
        params.append(start_date.isoformat())
    if end_date:
        conditions.append("date(started_at) <= ?")
        params.append(end_date.isoformat())

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM focus_sessions {where} ORDER BY started_at ASC",
            params,
        ).fetchall()

        # Per-day aggregation
        daily_rows = conn.execute(
            f"""SELECT
                    date(started_at) as day,
                    COUNT(*) as sessions,
                    SUM(completed) as completed,
                    SUM(duration_planned) as planned_min,
                    SUM(CASE WHEN completed THEN duration_actual ELSE 0 END) as actual_min
                FROM focus_sessions {where}
                GROUP BY day
                ORDER BY day ASC""",
            params,
        ).fetchall()

    total = len(rows)
    completed = sum(1 for r in rows if r["completed"])
    planned_min = sum(r["duration_planned"] for r in rows)
    actual_min = sum(
        (r["duration_actual"] or 0) for r in rows if r["completed"]
    )

    completion_pcts = [
        (r["duration_actual"] / r["duration_planned"] * 100)
        for r in rows
        if r["completed"] and r["duration_planned"] > 0 and r["duration_actual"]
    ]
    avg_completion = (
        sum(completion_pcts) / len(completion_pcts) if completion_pcts else 0.0
    )

    by_day = [
        {
            "day": r["day"],
            "sessions": r["sessions"],
            "completed": r["completed"],
            "planned_minutes": r["planned_min"],
            "actual_minutes": r["actual_min"],
        }
        for r in daily_rows
    ]

    return {
        "total_sessions": total,
        "completed_sessions": completed,
        "completion_rate": (completed / total * 100) if total else 0.0,
        "total_planned_minutes": planned_min,
        "total_actual_minutes": actual_min,
        "average_completion_pct": round(avg_completion, 1),
        "streak": FocusRepo.get_streak(),
        "by_day": by_day,
    }
