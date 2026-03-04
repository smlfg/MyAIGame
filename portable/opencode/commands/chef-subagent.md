---
name: chef-subagent
description: "Execute task in isolated session (non-blocking, separate context)"
argument-hint: "[task description]"
---

# /chef-subagent -- Isolated background execution

In OpenCode, this creates an isolated session that runs independently.

**Task:** $ARGUMENTS

## Process

1. **Tell user immediately:**
   > Spawning isolated session for: $ARGUMENTS. Continue working!

2. **Create isolated session:**
   Use `opencode_session_create(title="SubAgent: $ARGUMENTS")`
   Then send:
   ```
   Run: bash ~/.opencode/hooks/gather-context.sh "$(pwd)" "$ARGUMENTS"
   Then execute the task using that context.
   Report back: what was done, files modified, any issues.
   ```

3. **Continue conversation** -- don't block.

4. **When session completes**, report results (2-3 sentences).

## Rules
- NEVER block on the background session
- Use separate sessions for isolation
