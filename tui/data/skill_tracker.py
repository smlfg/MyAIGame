"""Tracks missed skill suggestions and logs them to ~/.claude/usage/missed-skills.jsonl."""

import json
from datetime import datetime, timezone
from pathlib import Path

USAGE_DIR = Path.home() / ".claude" / "usage"
MISSED_SKILLS_FILE = USAGE_DIR / "missed-skills.jsonl"

# Maps tool names to the skill that should have been suggested
SKILL_TRIGGERS: dict[str, str] = {
    "Edit": "/test",
    "Write": "/test",
    "chef": "/review",
    "Stop": "/recap",
    "Bash": "/review",
    "Read": "/check-state",
}


def check_missed(tool_name: str) -> str | None:
    """Return the suggested skill for a tool, or None if no suggestion exists."""
    return SKILL_TRIGGERS.get(tool_name)


def log_missed(tool: str, suggested_skill: str) -> None:
    """Log a missed skill suggestion to ~/.claude/usage/missed-skills.jsonl."""
    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": tool,
        "suggested_skill": suggested_skill,
    }
    with MISSED_SKILLS_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def get_missed_today() -> list[dict]:
    """Return all missed skill entries from today."""
    if not MISSED_SKILLS_FILE.exists():
        return []

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results: list[dict] = []

    with MISSED_SKILLS_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry_time = entry.get("time", "")
                if entry_time.startswith(today):
                    results.append(entry)
            except json.JSONDecodeError:
                continue

    return results
