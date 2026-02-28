---
argument-hint: [research query]
description: Delegate research to Gemini via SubAgent + MCP (non-blocking)
---

**Research SubAgent.** Query: **$ARGUMENTS**

## Process

1. **Tell user immediately:**
   > Researching via Gemini SubAgent: $ARGUMENTS. What else can I help with?

2. **Spawn SubAgent** via Task tool:
   - `subagent_type`: "general-purpose"
   - `model`: "haiku"
   - `run_in_background`: true
   - Prompt:
     ```
     Call mcp__gemini__ask-gemini with: "Research thoroughly: $ARGUMENTS. Provide: summary, key findings, code examples if applicable, best practices, reference URLs."
     Report back the structured findings.
     ```

3. **Continue conversation** — don't block.

4. **When SubAgent returns**, synthesize findings + add your analysis.

## Rules
- Haiku for SubAgent (Gemini does the heavy lifting)
- NEVER block on SubAgent
- Add your own commentary to Gemini's findings
