---
argument-hint: [task description]
description: Delegate task to OpenCode ASYNC via MCP - continue chatting while it runs
---

**Async delegation.** Task: **$ARGUMENTS**

## Process

1. **Gather context** (quick):
   Run `bash ~/.claude/hooks/gather-context.sh "$(pwd)" "$ARGUMENTS"` → capture as CONTEXT.

2. **Start async** via MCP:
   - `mcp__opencode__opencode_session_create(title="Async: $ARGUMENTS")`
   - `mcp__opencode__opencode_message_send_async(sessionId=..., prompt=CONTEXT)`

3. **Immediately tell user:**
   > Started async task! Session: [ID]. What else can I help with?

4. **When asked about status:**
   - `mcp__opencode__opencode_check(sessionId=...)` for progress
   - `mcp__opencode__opencode_review_changes(sessionId=...)` when done

## Rules
- Do NOT block waiting — return to user immediately after step 3
- Do NOT use synchronous `opencode_ask` — use async flow
- If MCP stalls >60s, tell user and offer to do it directly
