---
argument-hint: [research query]
description: Research via OpenCode MCP + WebFetch — Gemini-unabhaengiger Fallback-Researcher
---

**Research Mode (OpenCode).** Query: **$ARGUMENTS**

## Process

1. **Primary: OpenCode MCP** — Call `mcp__opencode__opencode_ask` with:
   - `prompt`:
     ```
     Research this topic thoroughly using web search:

     $ARGUMENTS

     Provide:
     - Summary (2-3 sentences)
     - Key findings (bullet points with source URLs)
     - Code examples (if applicable)
     - Best practices
     - Known gotchas or caveats
     - Reference URLs

     Use web search tools to find current information (2025-2026). German response preferred.
     ```
   - `directory`: Current working directory

2. **If OpenCode stalls >60s or fails:** Fallback to 3x `WebSearch` with different angles:
   - Search 1: `$ARGUMENTS official documentation 2025 2026`
   - Search 2: `$ARGUMENTS practical examples tutorial`
   - Search 3: `$ARGUMENTS common problems gotchas`
   Then use `WebFetch` on the top 2-3 most relevant URLs to get details.

3. **Present findings** with your own analysis added. Tell user which source was used (OpenCode / WebSearch+WebFetch / eigenes Wissen).

## Fallback Chain
1. OpenCode MCP (primary — has web search built in)
2. WebSearch + WebFetch (if OpenCode down)
3. Own knowledge (last resort, note: may be outdated)
