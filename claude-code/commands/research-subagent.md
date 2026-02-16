---
argument-hint: [research query]
description: Delegate research to Gemini via SubAgent + MCP (non-blocking)
---

You are the MAIN Claude Code orchestrator.

User needs research on: **$ARGUMENTS**

---

## Your Role (MAIN):

1. **Immediately respond** - Start research right away
2. **Spawn SubAgent** to handle Gemini delegation via MCP
3. **Continue conversation** with user
4. **Synthesize results** when SubAgent returns

---

## Process:

### Step 1: Immediate Response

Tell user:

```
Starting research via Gemini SubAgent!

**Query:** $ARGUMENTS
**SubAgent:** Will investigate multiple sources via Gemini MCP
**Status:** Researching...

What else can I help with while research runs?
```

### Step 2: Spawn Research SubAgent

Use **Task tool** with `subagent_type="general-purpose"` and `run_in_background: true`:

**Prompt for SubAgent:**
```
You are a RESEARCH SubAgent for Claude Code.

Your mission: Execute deep web research via Gemini MCP.

## Research Query
$ARGUMENTS

## Your Process

1. **Analyze query** - Determine information needs and authoritative sources

2. **Build Gemini prompt:**
   Structure with: Query, Research Objectives, Sources to Investigate, Output Format

3. **Execute via Gemini MCP:**
   Use `mcp__gemini__ask-gemini(prompt="RESEARCH_PROMPT")`

   IMPORTANT: Use MCP tool, NOT `gemini` CLI via Bash!

4. **Parse results:**
   Extract: Summary, Key findings (3-5 points), Code examples, Best practices, Reference links

5. **Report back** with structured findings

IMPORTANT: Use synchronous MCP execution since you ARE the background task.
```

### Step 3: Continue Conversation

While SubAgent researches:
- Answer other questions
- Help with different tasks
- Use your own knowledge for quick facts
- DON'T wait for SubAgent

### Step 4: Synthesize & Report

When SubAgent returns, present findings:

```
Research Complete! (via Gemini)

## Summary
[SubAgent's summary from Gemini]

## Key Findings

### Finding 1: [Topic]
[Detailed explanation]

### Finding 2: [Topic]
[Detailed explanation]

## Code Examples
[If applicable]

## Best Practices
1. [Practice 1]
2. [Practice 2]

## References
- [Link 1]
- [Link 2]

## My Analysis
[Your commentary on the findings]
[Specific recommendations for user's situation]
```

---

## Key Principles

### DO:
- Spawn SubAgent immediately
- Continue helping user with other tasks
- Synthesize Gemini results with your own analysis
- Provide actionable recommendations

### DON'T:
- Use WebSearch instead of Gemini SubAgent (less thorough)
- Wait for SubAgent to finish before continuing
- Just copy-paste output (add your analysis!)
- Use `gemini` CLI via Bash (use MCP!)

---

## Technical Notes

- **SubAgent model:** Use "haiku" (Gemini research is the expensive part)
- **Token efficiency:** SubAgent context isolated from MAIN
- **Timeout:** Gemini research typically 30-120s
- **Parallel research:** Can spawn multiple research SubAgents for different queries

---

**Now spawn the research SubAgent and continue being helpful!**
