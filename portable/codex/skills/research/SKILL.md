---
name: research
description: "Research a topic using web search for deep analysis"
argument-hint: "[research query]"
category: research
cost-tier: low
dependencies:
  tools: [research]
tags: [research, web-search, analysis]
---

# /research -- Deep Web Research

**Research Mode.** Query: **$ARGUMENTS**

## Process

1. {{research(query="""
   Research thoroughly: $ARGUMENTS

   Provide:
   - Summary (2-3 sentences)
   - Key findings (bullet points)
   - Code examples (if applicable)
   - Best practices
   - Reference URLs
   """)}}

2. **Present findings** with your own analysis added.

## Fallback
1. Web search / MCP research (primary)
2. Built-in web search tool (if primary stalls >60s)
3. Own knowledge (note: may be outdated)

Tell user which source was used.
