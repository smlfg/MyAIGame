---
name: chef-async
description: "Execute task in background session -- continue chatting while it runs"
argument-hint: "[task description]"
---

# /chef-async -- Background task execution

In OpenCode, this creates a separate session for the task so you can continue working.

**Task:** $ARGUMENTS

## Process

1. **Gather context** (quick):
   Run `bash ~/.opencode/hooks/gather-context.sh "$(pwd)" "$ARGUMENTS"` and capture as CONTEXT.

2. **Create a new session** for this task:
   Use `opencode_session_create(title="Async: $ARGUMENTS")`
   Then `opencode_message_send_async(sessionId=..., prompt=CONTEXT + task)`

3. **Immediately tell user:**
   > Started background task! Session: [ID]. Continue working -- check with /check-session [ID].

4. **When asked about status:**
   - `opencode_check(sessionId=...)` for progress
   - `opencode_review_changes(sessionId=...)` when done

## Rules
- Do NOT block waiting -- return to user immediately after step 3
- Use async flow for true non-blocking execution
