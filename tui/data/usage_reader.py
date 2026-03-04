"""Reads ~/.claude/usage/YYYY-MM-DD.jsonl files and returns usage statistics."""

import json
from datetime import datetime, timezone
from pathlib import Path

USAGE_DIR = Path.home() / ".claude" / "usage"

# Rough cost estimate per tool call in USD (very approximate)
COST_PER_CALL = 0.003


def _get_jsonl_path(date: datetime | None = None) -> Path:
    if date is None:
        date = datetime.now(timezone.utc)
    return USAGE_DIR / f"{date.strftime('%Y-%m-%d')}.jsonl"


def get_today_usage() -> dict[str, int]:
    """Read today's JSONL, return {tool: count}."""
    path = _get_jsonl_path()
    counts: dict[str, int] = {}
    if not path.exists():
        return counts
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                tool = entry.get("tool", "unknown")
                counts[tool] = counts.get(tool, 0) + 1
            except json.JSONDecodeError:
                continue
    return counts


def get_top_n(n: int = 5, date: datetime | None = None) -> list[tuple[str, int]]:
    """Return top N tools by usage count for a given date (defaults to today)."""
    path = _get_jsonl_path(date)
    counts: dict[str, int] = {}
    if not path.exists():
        return []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                tool = entry.get("tool", "unknown")
                counts[tool] = counts.get(tool, 0) + 1
            except json.JSONDecodeError:
                continue
    sorted_tools = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_tools[:n]


def get_daily_summary(date: datetime | None = None) -> dict:
    """Return session count, total tools used, and cost estimate for a date."""
    path = _get_jsonl_path(date)
    total_calls = 0
    tools_seen: set[str] = set()

    if not path.exists():
        return {
            "total_calls": 0,
            "unique_tools": 0,
            "cost_estimate_usd": 0.0,
            "date": (date or datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
        }

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                total_calls += 1
                tools_seen.add(entry.get("tool", "unknown"))
            except json.JSONDecodeError:
                continue

    return {
        "total_calls": total_calls,
        "unique_tools": len(tools_seen),
        "cost_estimate_usd": round(total_calls * COST_PER_CALL, 4),
        "date": (date or datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
    }
