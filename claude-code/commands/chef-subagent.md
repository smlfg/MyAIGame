---
argument-hint: [task description]
description: Delegate to OpenCode via SubAgent + MCP (non-blocking, isolated context)
---

**SubAgent delegation.** Task: **$ARGUMENTS**

## Process

1. **Tell user immediately:**
   > Spawning SubAgent for: $ARGUMENTS. What else can I help with?

2. **Spawn SubAgent** via Task tool:
   - `subagent_type`: "general-purpose"
   - `model`: "haiku"
   - `run_in_background`: true
   - Prompt:
     ```
     Run: bash ~/.claude/hooks/gather-context.sh "$(pwd)" "$ARGUMENTS"
     Then call mcp__opencode__opencode_ask with that output as prompt and directory="$(pwd)".
     Report back: what was done, files modified, any issues.
     ```

3. **Continue conversation** — don't block.

4. **When SubAgent returns**, report results (2-3 sentences).

## Rules
- Use Haiku for SubAgent (cheap + fast)
- NEVER block on SubAgent
- NEVER read files yourself — SubAgent + script handle it
