---
name: chef-async
description: "Delegate task ASYNC -- continue chatting while it runs"
argument-hint: "[task description]"
category: delegation
cost-tier: low
dependencies:
  tools: [delegate_code_async, shell, check_session, review_changes]
  scripts: ["gather-context.sh"]
tags: [async, non-blocking, delegation]
---

# /chef-async -- Async Delegation

**Async delegation.** Task: **$ARGUMENTS**

## Process

1. **Gather context** (quick):
   {{gather_context(dir=project_dir, task="$ARGUMENTS")}}
   Capture as CONTEXT.

2. **Start async session:**
   {{delegate_code_session(title="Async: $ARGUMENTS", dir=project_dir)}}
   Then send CONTEXT as async message to the session.

3. **Immediately tell user:**
   > Started async task! Session: [ID]. What else can I help with?

4. **When asked about status:**
   - {{check_session(sessionId)}} for progress
   - {{review_changes(sessionId)}} when done

## Rules
- Do NOT block waiting -- return to user immediately after step 3
- Do NOT use synchronous delegation -- use async flow
- If execution stalls >60s, tell user and offer to do it directly

## Codex Limitation
Codex CLI does not have native async session management. Workaround: Use `codex --quiet` in background via shell, or use MCP server threads for async execution. The skill may need to fall back to synchronous execution.
