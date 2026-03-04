---
name: crew
description: "Delegate to CrewAI manager with cheap workers (multi-agent orchestration)"
argument-hint: "[task description]"
category: multi-agent
cost-tier: high
dependencies:
  tools: [shell, file_read]
  external: ["crew_unified.py"]
tags: [multi-agent, crewai, orchestration]
---

# /crew -- CrewAI Multi-Agent Delegation

You are now delegating this task to the **CrewAI Middle Manager**.

## Task: $ARGUMENTS

---

## IMPORTANT: External Dependency Required!

This command requires `crew_unified.py` to be installed.

**Check if it exists first:**
{{shell("ls -la ~/.claude/scripts/crew_unified.py")}}

If it doesn't exist, tell the user:
```
crew_unified.py is not installed yet.
This script orchestrates CrewAI with cheap manager and workers.
Alternative: Use /chef or /chef-subagent instead (more expensive but works out of the box).
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

{{shell("python3 ~/.claude/scripts/crew_unified.py \"$ARGUMENTS\"")}}

For professional mode: add `--mode=pro`

### Step 4: VERIFY & REPORT

Check results and summarize for user.

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

## Codex Limitation
The external `crew_unified.py` dependency works the same way in Codex (executed via shell). However, the CrewAI script uses its own LLM providers internally, independent of Codex's execution model.
