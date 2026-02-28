---
argument-hint: [task description]
description: Delegate to CrewAI manager with Gemini+MiniMax workers (cheap orchestration)
---

You are now delegating this task to the **CrewAI Middle Manager**.

## Architecture

```
MainClaudeCodeSession (You - Strategy Only)
    |
CrewAI Manager (Gemini Flash - $0.10/1M tokens)
    | | |
Worker 1      Worker 2      Worker 3
(MiniMax)     (MiniMax)     (MiniMax)
    |             |             |
OpenCode      OpenCode      OpenCode
```

## Task: $ARGUMENTS

---

## IMPORTANT: External Dependency Required!

This command requires `crew_unified.py` to be installed at `~/.claude/scripts/crew_unified.py`.

**Check if it exists first:**
```bash
ls -la ~/.claude/scripts/crew_unified.py
```

If it doesn't exist, tell the user:
```
crew_unified.py is not installed yet.

This script orchestrates CrewAI with Gemini Flash as manager and MiniMax as workers.
It needs to be set up separately — it's not part of the base MCP system.

Alternative: Use /chef or /chef-subagent instead (uses Claude SubAgents, more expensive but works out of the box).
```

---

## If crew_unified.py IS available:

### Step 1: GATHER CONTEXT FIRST (MANDATORY!)

Before calling Crew, you MUST:
1. **Explore the codebase** - Find relevant files, read key files
2. **Understand the project** - What frameworks, patterns, conventions?
3. **Clarify vague requirements** - Ask user for specifics if ambiguous

### Step 2: BUILD DETAILED PROMPT

Transform user request into actionable specification with project context, current state, concrete tasks, constraints, and success criteria.

### Step 3: EXECUTE

```bash
python3 ~/.claude/scripts/crew_unified.py "$ARGUMENTS"

# Professional mode (retry logic, metrics):
python3 ~/.claude/scripts/crew_unified.py "$ARGUMENTS" --mode=pro
```

### Step 4: VERIFY & REPORT

Check results and summarize for user.

---

## Cost Comparison

| Approach | Manager Cost | Worker Cost | Total/1M tokens |
|----------|-------------|-------------|-----------------|
| **CrewAI** (this) | $0.10 (Gemini Flash) | $0.50 (MiniMax) | ~$0.60 |
| **SubAgents** (/chef-subagent) | Free (Claude main) | $3.00 (Claude Sonnet) | ~$3.00 |
| **Savings** | | | **80%** |

---

## When to Use

### Use /crew when:
- Multi-file refactoring
- Feature implementation (3+ files)
- Complex changes requiring coordination
- You want to save tokens

### Don't use /crew when:
- Simple single-file edits (use /chef)
- Quick bug fixes
- Just reading/analyzing code
- crew_unified.py is not installed

---

**Now execute the delegation and report back to the user!**
