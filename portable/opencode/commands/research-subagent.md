---
name: research-subagent
description: "Non-blocking research via background session"
argument-hint: "[research query]"
---

# /research-subagent -- Background Research

**Research SubAgent.** Query: **$ARGUMENTS**

## Process

1. **Tell user immediately:**
   > Researching in background: $ARGUMENTS. Continue working!

2. **Create background research session:**
   Use `opencode_session_create(title="Research: $ARGUMENTS")`
   Then send async:
   ```
   Research thoroughly: $ARGUMENTS
   Provide: summary, key findings, code examples if applicable, best practices, reference URLs.
   ```

3. **Continue conversation** -- don't block.

4. **When session completes**, synthesize findings + add your analysis.

## Rules
- NEVER block on the background session
- Add your own commentary to the research findings
