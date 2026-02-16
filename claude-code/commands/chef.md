---
argument-hint: [task description]
description: Delegate coding task to OpenCode via MCP with enhanced prompting (Manager Mode)
---

You are now in **Manager Mode** (not coding mode).

The user has delegated this task to you as a manager:

**User Request:** $ARGUMENTS

---

## Your Role as Manager:

1. **Analyze the request** - Understand what the user wants
2. **Enhance the prompt** - Add context, structure, and clarity
3. **Delegate to OpenCode** - Your executive agent that does the implementation
4. **Report back** - Summarize what OpenCode accomplished

---

## Process:

### 1. Gather Context (MANDATORY!)

Before delegating, YOU must:
- Use Read/Glob/Grep tools to check relevant files
- Note current working directory
- Identify related components and dependencies
- Understand existing patterns and conventions

### 2. Build Enhanced Prompt

Transform the user's request into a structured, actionable prompt:

```
# PROJECT CONTEXT
Project: [name from current directory]
Location: [pwd]
Stack: [detected from package.json/requirements.txt/docker-compose.yml]

# CURRENT STATE
[What you learned from context gathering]

# TASK
[Enhanced version of user's request with specific details]

# REQUIREMENTS
- Follow existing code patterns
- One task, one file, one change
- Add tests where appropriate

# FILES TO CONSIDER
[List specific files if relevant]

# SUCCESS CRITERIA
[What "done" looks like - be specific]
```

### 3. Delegate via MCP

**Use the OpenCode MCP tool — NOT Bash/shell:**

**Simple tasks (one-shot):**
Use `mcp__opencode__opencode_ask` with your enhanced prompt and the project directory.

**Complex tasks (multi-step):**
1. Create a session: `mcp__opencode__opencode_session_create`
2. Send first step: `mcp__opencode__opencode_message_send`
3. Review changes: `mcp__opencode__opencode_review_changes`
4. Continue if needed: `mcp__opencode__opencode_reply`

**IMPORTANT:**
- ALWAYS use MCP tools, NEVER `opencode run` via Bash
- ALWAYS set the `directory` parameter to the current project path
- Use `--format json` equivalent by parsing MCP response directly

### 4. Parse Output & Verify

After OpenCode responds:
- Check what files were modified
- Read modified files to verify quality
- Run tests if applicable
- Check for regressions

### 5. Report to User

Summarize:
- What OpenCode accomplished
- Files modified
- Any issues or blockers
- Actionable next steps

---

## Fallback:

If OpenCode MCP doesn't respond within 60 seconds:
- Do the task directly
- Tell user: "OpenCode MCP not responding — handling this directly."

---

## Anti-patterns:
- NEVER delegate without gathering context first
- NEVER send vague one-liners ("fix the bug") — be specific
- NEVER use `opencode run` via Bash — use MCP tools
- NEVER skip verification of the result
- NEVER forget the `directory` parameter

---

**Now execute: gather context, enhance prompt, delegate via MCP, verify, report.**
