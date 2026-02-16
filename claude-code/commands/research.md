---
argument-hint: [research query]
description: Research a topic using Gemini via MCP for deep web search and analysis
---

You are now in **Research Coordinator Mode**.

The user needs web research on:

**Research Query:** $ARGUMENTS

---

## CRITICAL: Use Gemini MCP, NOT WebSearch!

For web research, ALWAYS use the Gemini MCP tool (`mcp__gemini__ask-gemini`).

**Why Gemini over WebSearch?**
- Gemini can browse and read full web pages (not just snippets)
- Gemini synthesizes information from multiple sources
- Gemini has a massive context window for analyzing large docs
- WebSearch only returns search result summaries

---

## Process:

### 1. Analyze the Query

Determine:
- What type of information? (technical docs, news, comparisons, troubleshooting)
- Which sources are authoritative?
- How deep should the research go?

### 2. Build Research Prompt

Structure your prompt for Gemini:

```
# WEB RESEARCH REQUEST

## Query
[User's original query]

## Research Objectives
1. [Specific objective 1]
2. [Specific objective 2]
3. [Specific objective 3]

## Sources to Investigate
Please thoroughly check:
- [URL/site 1]: [What to look for]
- [URL/site 2]: [What to look for]

## What I Need
- Comprehensive summary (not just snippets)
- Code examples (if applicable)
- Best practices
- Common pitfalls/warnings
- Links to relevant pages

## Output Format
### Summary (2-3 sentences)
### Key Findings (bullet points)
### Code Examples (if applicable)
### Best Practices
### References (URLs)
```

### 3. Execute via Gemini MCP

**Use `mcp__gemini__ask-gemini`** with your research prompt.

**IMPORTANT:**
- Do NOT use WebSearch as primary tool
- Do NOT use `gemini` CLI via Bash
- Use the MCP tool directly

### 4. Synthesize & Present

Present findings to user:

```
## Research Results (via Gemini)

### Summary
[2-3 sentence overview]

### Key Findings
- [Finding 1]
- [Finding 2]
- [Finding 3]

### Code Examples
[If applicable]

### Best Practices
1. [Practice 1]
2. [Practice 2]

### References
- [Link 1]
- [Link 2]

### My Analysis
[Your brief commentary — add context from your own knowledge]
[Specific recommendations for the user's situation]
```

---

## Fallback Strategy

1. **Primary:** Gemini MCP (`mcp__gemini__ask-gemini`)
2. **If Gemini fails (>60s):** Use Claude's native WebSearch + WebFetch
3. **If WebSearch fails:** Use your own knowledge (note that it may be outdated)

Tell user which method was used.

---

## When to Use /research vs Other Tools

### Use /research (Gemini) when:
- Comprehensive investigation across multiple sources
- Technical documentation deep dive
- Comparing multiple options
- Need code examples from the web

### Don't use /research when:
- Quick fact check (use WebSearch directly)
- Internal codebase questions (use Grep/Read)
- Something you already know

---

**Now research the topic via Gemini MCP and report findings!**
