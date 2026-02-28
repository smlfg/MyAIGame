---
argument-hint: [task description]
description: Direct OpenCode delegation — minimal overhead, no context gathering
---

Delegate directly to OpenCode. No context gathering, no enhancement. For quick tasks where OpenCode can figure it out.

Call `mcp__opencode__opencode_ask` with:
- `prompt`: "$ARGUMENTS"
- `directory`: Current working directory

Report the result in 1-2 sentences. If MCP stalls >60s, do it directly.
