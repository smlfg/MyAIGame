#!/usr/bin/env bash
# session-extract.sh — Extract last N messages from Claude Code session JSONL
# Usage: session-extract.sh [session_file] [num_messages]
#
# Parses the JSONL transcript to get recent conversation context.
# Output: Compact summary of recent messages (role + first 200 chars)

set -euo pipefail

SESSION_FILE="${1:-}"
NUM_MESSAGES="${2:-10}"

if [[ -z "$SESSION_FILE" ]] || [[ ! -f "$SESSION_FILE" ]]; then
    echo "# No session transcript available"
    exit 0
fi

echo "# Recent Session Context (last $NUM_MESSAGES messages)"
echo ""

# Extract messages — each line is a JSON object
# We want: role (human/assistant), first ~200 chars of content
tail -n 200 "$SESSION_FILE" | \
    python3 -c "
import sys, json

messages = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        obj = json.loads(line)
        # Claude Code JSONL format: look for message objects
        role = obj.get('role', obj.get('type', ''))

        # Extract text content
        content = ''
        if isinstance(obj.get('content'), str):
            content = obj['content']
        elif isinstance(obj.get('content'), list):
            for block in obj['content']:
                if isinstance(block, dict) and block.get('type') == 'text':
                    content += block.get('text', '')
                elif isinstance(block, str):
                    content += block

        if role and content:
            messages.append((role, content[:200]))
    except (json.JSONDecodeError, KeyError):
        continue

# Last N messages
for role, text in messages[-${NUM_MESSAGES}:]:
    text_clean = text.replace('\n', ' ').strip()
    print(f'**{role}**: {text_clean}')
    print()
" 2>/dev/null || echo "# Could not parse session file"
