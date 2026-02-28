---
argument-hint: [task description]
description: Delegate coding task to OpenCode via MCP with enhanced prompting (Manager Mode)
---

You are in **Manager Mode**. Task: **$ARGUMENTS**

## Process

1. **Gather context via script** (zero LLM tokens):
   Run `bash ~/.claude/hooks/gather-context-enhanced.sh "$(pwd)" "$ARGUMENTS"` and capture output as CONTEXT.

2. **Delegate to OpenCode** via MCP:
   Call `mcp__opencode__opencode_ask` with:
   - `prompt`: The full CONTEXT output from step 1, followed by:
     ```
     # REQUIREMENTS
     - Follow existing code patterns in this project
     - One task, one change, keep it focused
     - Add tests where appropriate

     # SUCCESS CRITERIA
     Task is done when: [infer from task what "done" looks like]
     ```
   - `directory`: Current working directory (pwd)

3. **Report** (2-3 sentences max):
   - What was done
   - Files modified
   - Any blockers or next steps

## Rules
- NEVER read files yourself — the script does it for $0
- NEVER use `opencode run` via Bash — use MCP tools
- If MCP stalls >60s, do the task directly and tell user
- ALWAYS set `directory` parameter
