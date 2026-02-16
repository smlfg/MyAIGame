---
argument-hint: [task description]
description: Delegate task to OpenCode ASYNC via MCP - continue chatting while it runs
---

You are now in **Async Manager Mode**.

The user has delegated this task to run in the background:

**User Request:** $ARGUMENTS

---

## Your Role as Async Manager:

1. **Start OpenCode async** - Non-blocking execution via MCP
2. **Immediately return to user** - Let them continue working
3. **Report when done** - Show results when available

---

## Process:

### Step 1: Gather Context (Quick!)

Quickly check the most relevant files for the task. Don't over-research — this is async, speed matters.

### Step 2: Build Enhanced Prompt

Same structure as `/chef` but keep it concise since this runs in the background.

### Step 3: Send Async via MCP

**Use `mcp__opencode__opencode_message_send_async`** to start the task without blocking:

1. Create a session: `mcp__opencode__opencode_session_create(title="Async: [task summary]")`
2. Send async: `mcp__opencode__opencode_message_send_async(sessionId="...", prompt="ENHANCED_PROMPT")`
3. Note the session ID for later checking

**IMPORTANT:** Do NOT use `opencode_ask` (that's synchronous). Use the async message flow.

### Step 4: Immediately Notify User

Tell the user RIGHT AWAY:

```
Started OpenCode async task!

**Task:** [Brief description]
**Session:** [session ID]
**Status:** Running in background...

What else can I help with while that runs?
```

### Step 5: Continue Conversation

While OpenCode works in the background:
- Answer user's other questions
- Help with different tasks
- DON'T block waiting for OpenCode

### Step 6: Check & Report When Asked

When user asks about status, or when you naturally have a pause:
- Use `mcp__opencode__opencode_session_status(sessionId="...")` to check
- Use `mcp__opencode__opencode_wait(sessionId="...")` if you want to wait for completion
- Report results when done

---

## When to Use

### Use `/chef-async` when:
- Task takes >60s
- You want to continue working on other things
- Multiple parallel tasks needed
- Not urgent (can wait for results)

### Use `/chef` (synchronous) when:
- Task is quick (<30s)
- You need the result immediately
- Single focused task

---

## Fallback:

If OpenCode MCP doesn't respond within 60 seconds:
- Tell user: "OpenCode MCP not responding — will handle directly when ready."

---

**Now: gather context quickly, send async via MCP, notify user, continue conversation!**
