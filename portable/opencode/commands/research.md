---
name: research
description: "Research a topic using web search for deep analysis"
argument-hint: "[research query]"
---

# /research -- Web Research Mode

**Research Mode.** Query: **$ARGUMENTS**

## Process

1. Use built-in web search or configured research MCP with prompt:
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
1. Web search (primary)
2. Own knowledge (note: may be outdated)

Tell user which source was used.
