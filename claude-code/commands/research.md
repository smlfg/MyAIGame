---
argument-hint: [research query]
description: Research a topic using Gemini via MCP for deep web search and analysis
---

**Research Mode.** Query: **$ARGUMENTS**

## Process

1. Call `mcp__gemini__ask-gemini` with prompt:
   ```
   Research thoroughly: $ARGUMENTS

   Provide:
   - Summary (2-3 sentences)
   - Key findings (bullet points)
   - Code examples (if applicable)
   - Best practices
   - Reference URLs
   ```

2. **Present findings** with your own analysis added.

## Fallback
1. Gemini MCP (primary)
2. WebSearch + WebFetch (if Gemini stalls >60s)
3. Own knowledge (note: may be outdated)

Tell user which source was used.
