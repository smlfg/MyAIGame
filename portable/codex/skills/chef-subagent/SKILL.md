---
name: chef-subagent
description: "Delegate to execution engine via sub-agent (non-blocking, isolated context)"
argument-hint: "[task description]"
category: delegation
cost-tier: low
dependencies:
  tools: [spawn_subagent, delegate_code, shell]
  scripts: ["gather-context.sh"]
tags: [subagent, non-blocking, isolated]
---

# /chef-subagent -- SubAgent Delegation

**SubAgent delegation.** Task: **$ARGUMENTS**

## Process

1. **Tell user immediately:**
   > Spawning SubAgent for: $ARGUMENTS. What else can I help with?

2. **Spawn SubAgent:**
   {{spawn_subagent(model="lightweight", prompt="""
   Run: gather-context.sh on project directory for "$ARGUMENTS"
   Then delegate to code execution engine with that output as prompt.
   Report back: what was done, files modified, any issues.
   """)}}

3. **Continue conversation** -- don't block.

4. **When SubAgent returns**, report results (2-3 sentences).

## Rules
- Use lightweight model for SubAgent (cheap + fast)
- NEVER block on SubAgent
- NEVER read files yourself -- SubAgent + script handle it

## Codex Limitation
Codex does not have native sub-agent spawning like Claude Code's Task tool. Workaround: Use `codex mcp-server` to create threads, or run a separate `codex` process in background via shell. The non-blocking behavior may be limited.
