#!/usr/bin/env bash
# gather-context.sh — Collects project context for delegation ($0 in LLM tokens)
# Usage: gather-context.sh [project_dir] [task_description]
#
# Output: Structured context block ready to paste into an LLM prompt

set -euo pipefail

PROJECT_DIR="${1:-.}"
TASK="${2:-no task specified}"

# Resolve to absolute path
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

echo "# PROJECT CONTEXT"
echo ""
echo "## Directory"
echo "$PROJECT_DIR"
echo ""

# --- Stack Detection ---
echo "## Stack"
if [[ -f "$PROJECT_DIR/package.json" ]]; then
    echo "- Node.js ($(jq -r '.name // "unnamed"' "$PROJECT_DIR/package.json"))"
    # Key deps
    jq -r '.dependencies // {} | keys[]' "$PROJECT_DIR/package.json" 2>/dev/null | head -10 | sed 's/^/  - /'
fi
if [[ -f "$PROJECT_DIR/requirements.txt" ]]; then
    echo "- Python (requirements.txt)"
    head -5 "$PROJECT_DIR/requirements.txt" | sed 's/^/  - /'
fi
if [[ -f "$PROJECT_DIR/pyproject.toml" ]]; then
    echo "- Python (pyproject.toml)"
fi
if [[ -f "$PROJECT_DIR/Cargo.toml" ]]; then
    echo "- Rust"
fi
if [[ -f "$PROJECT_DIR/go.mod" ]]; then
    echo "- Go"
fi
if [[ -f "$PROJECT_DIR/docker-compose.yml" ]] || [[ -f "$PROJECT_DIR/docker-compose.yaml" ]]; then
    echo "- Docker Compose"
fi
echo ""

# --- Git State ---
if git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    echo "## Git State"
    BRANCH=$(git -C "$PROJECT_DIR" branch --show-current 2>/dev/null || echo "detached")
    echo "- Branch: $BRANCH"

    # Uncommitted changes summary
    CHANGED=$(git -C "$PROJECT_DIR" diff --stat 2>/dev/null | tail -1)
    if [[ -n "$CHANGED" ]]; then
        echo "- Uncommitted: $CHANGED"
    else
        echo "- Working tree clean"
    fi

    # Recent commits (last 5)
    echo "- Recent commits:"
    git -C "$PROJECT_DIR" log --oneline -5 2>/dev/null | sed 's/^/  /'
    echo ""

    # Changed files (for task relevance)
    DIFF_FILES=$(git -C "$PROJECT_DIR" diff --name-only 2>/dev/null)
    if [[ -n "$DIFF_FILES" ]]; then
        echo "## Changed Files (uncommitted)"
        echo "$DIFF_FILES" | sed 's/^/- /'
        echo ""
    fi
fi

# --- Directory Structure (compact) ---
echo "## Structure (top 2 levels)"
if command -v tree &>/dev/null; then
    tree -L 2 --dirsfirst -I 'node_modules|venv|.venv|__pycache__|.git|dist|build|.next' "$PROJECT_DIR" 2>/dev/null | head -40
else
    find "$PROJECT_DIR" -maxdepth 2 -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' -not -path '*/venv/*' 2>/dev/null | head -40
fi
echo ""

# --- Task-Relevant Files (if git diff shows changes) ---
if [[ -n "${DIFF_FILES:-}" ]]; then
    echo "## File Contents (changed files, first 50 lines each)"
    echo "$DIFF_FILES" | head -5 | while read -r f; do
        if [[ -f "$PROJECT_DIR/$f" ]]; then
            echo "### $f"
            echo '```'
            head -50 "$PROJECT_DIR/$f"
            echo '```'
            echo ""
        fi
    done
fi

echo "## TASK"
echo "$TASK"
