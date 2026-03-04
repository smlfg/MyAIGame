---
name: research-subagent
description: "Delegate research to web search via sub-agent (non-blocking)"
argument-hint: "[research query]"
category: research
cost-tier: low
dependencies:
  tools: [spawn_subagent, research]
tags: [research, non-blocking, subagent]
---

# /research-subagent -- Non-Blocking Research

**Research SubAgent.** Query: **$ARGUMENTS**

## Process

1. **Tell user immediately:**
   > Researching via SubAgent: $ARGUMENTS. What else can I help with?

2. **Spawn SubAgent:**
   {{spawn_subagent(model="lightweight", prompt="""
   Research thoroughly: $ARGUMENTS
   Provide: summary, key findings, code examples if applicable, best practices, reference URLs.
   Report back the structured findings.
   """)}}

3. **Continue conversation** -- don't block.

4. **When SubAgent returns**, synthesize findings + add your analysis.

## Rules
- Use lightweight model for SubAgent (research engine does the heavy lifting)
- NEVER block on SubAgent
- Add your own commentary to the research findings

## Codex Limitation
Codex does not have native sub-agent spawning. Workaround: Use `codex mcp-server` threads or run a background shell process. Alternatively, use /research (synchronous) as a simpler fallback.
