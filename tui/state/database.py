"""SQLite database manager for TUI state persistence."""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# Schema version for migrations
SCHEMA_VERSION = 1

DB_PATH = Path.home() / ".local" / "share" / "myaigame" / "state.db"


def _get_db_path() -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


_local = threading.local()


def _get_connection() -> sqlite3.Connection:
    """Get or create a thread-local connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(str(_get_db_path()), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn = conn
    return _local.conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database access."""
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db() -> None:
    """Initialize the database and run migrations."""
    with get_db() as conn:
        _run_migrations(conn)


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Apply schema migrations in order."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    current_version = row[0] or 0

    if current_version < 1:
        _migrate_v1(conn)
        conn.execute("INSERT INTO schema_version (version) VALUES (1)")


def _migrate_v1(conn: sqlite3.Connection) -> None:
    """Initial schema."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            goal TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            provider TEXT NOT NULL DEFAULT '',
            total_cost REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tokens_in INTEGER NOT NULL DEFAULT 0,
            tokens_out INTEGER NOT NULL DEFAULT 0,
            cost REAL NOT NULL DEFAULT 0.0
        );
        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);

        CREATE TABLE IF NOT EXISTS skill_invocations (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            skill_name TEXT NOT NULL,
            provider TEXT NOT NULL,
            cost REAL NOT NULL DEFAULT 0.0,
            duration_ms INTEGER NOT NULL DEFAULT 0,
            success INTEGER NOT NULL DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_skills_session ON skill_invocations(session_id);

        CREATE TABLE IF NOT EXISTS focus_sessions (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            goal TEXT NOT NULL,
            started_at TEXT NOT NULL,
            duration_planned INTEGER NOT NULL,
            duration_actual INTEGER,
            completed INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_focus_session ON focus_sessions(session_id);

        CREATE TABLE IF NOT EXISTS parked_distractions (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,
            promoted_to_task INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_distractions_session ON parked_distractions(session_id);

        CREATE TABLE IF NOT EXISTS checkpoints (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            git_hash TEXT NOT NULL,
            summary TEXT NOT NULL,
            files_changed INTEGER NOT NULL DEFAULT 0,
            tests_passed INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_checkpoints_session ON checkpoints(session_id);

        CREATE TABLE IF NOT EXISTS cost_events (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            tokens_in INTEGER NOT NULL DEFAULT 0,
            tokens_out INTEGER NOT NULL DEFAULT 0,
            cost REAL NOT NULL DEFAULT 0.0,
            timestamp TEXT NOT NULL,
            context TEXT NOT NULL DEFAULT 'message'
        );
        CREATE INDEX IF NOT EXISTS idx_costs_session ON cost_events(session_id);
        CREATE INDEX IF NOT EXISTS idx_costs_timestamp ON cost_events(timestamp);
    """)


def close_db() -> None:
    """Close the thread-local connection."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None
