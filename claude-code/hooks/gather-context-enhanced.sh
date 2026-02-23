#!/bin/bash
# gather-context-enhanced.sh — Extended context with keyword auto-detection
# Usage: gather-context-enhanced.sh <dir> "<task>"

DIR="${1:-.}"
TASK="${2:-}"

# Basis-Context zuerst
~/.claude/hooks/gather-context.sh "$DIR" "$TASK"

TASK_LOWER=$(echo "$TASK" | tr '[:upper:]' '[:lower:]')

echo ""
echo "=== AUTO-DETECTED CONTEXT ==="

if echo "$TASK_LOWER" | grep -qE "config|settings|env|\.env"; then
    echo "--- src/config.py ---"
    head -60 "$DIR/src/config.py" 2>/dev/null
    echo "--- .env.example ---"
    head -20 "$DIR/.env.example" 2>/dev/null
fi

if echo "$TASK_LOWER" | grep -qE "test|conftest|pytest|coverage"; then
    echo "--- tests/conftest.py ---"
    cat "$DIR/tests/conftest.py" 2>/dev/null
    echo "--- pytest.ini ---"
    cat "$DIR/pytest.ini" 2>/dev/null
fi

if echo "$TASK_LOWER" | grep -qE "api|endpoint|route|fastapi"; then
    echo "--- src/api/main.py (first 80 lines) ---"
    head -80 "$DIR/src/api/main.py" 2>/dev/null
fi

if echo "$TASK_LOWER" | grep -qE "database|db|model|schema|migration"; then
    echo "--- src/services/database.py (first 80 lines) ---"
    head -80 "$DIR/src/services/database.py" 2>/dev/null
fi

if echo "$TASK_LOWER" | grep -qE "keepa|deal|price|api.client"; then
    echo "--- src/services/keepa_api.py (first 60 lines) ---"
    head -60 "$DIR/src/services/keepa_api.py" 2>/dev/null
fi

if echo "$TASK_LOWER" | grep -qE "schedule|cron|job|scheduler"; then
    echo "--- src/scheduler.py (first 60 lines) ---"
    head -60 "$DIR/src/scheduler.py" 2>/dev/null
fi

echo "=== END AUTO-DETECTED CONTEXT ==="
