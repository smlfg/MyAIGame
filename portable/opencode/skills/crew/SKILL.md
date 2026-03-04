---
name: crew
description: "Delegate to CrewAI manager with external workers (cheap orchestration)"
argument-hint: "[task description]"
category: multi-agent
cost-tier: high
dependencies:
  tools: [shell]
  external: ["crew_unified.py"]
tags: [multi-agent, crewai, orchestration]
---

# /crew -- CrewAI Multi-Agent Delegation

You are now delegating this task to the **CrewAI Middle Manager**.

## Task: $ARGUMENTS

---

## IMPORTANT: External Dependency Required!

This command requires `crew_unified.py` to be installed at `~/.opencode/scripts/crew_unified.py`.

**Check if it exists first:**
```bash
ls -la ~/.opencode/scripts/crew_unified.py
```

If it doesn't exist, tell the user:
```
crew_unified.py is not installed yet.

This script orchestrates CrewAI with external workers.
It needs to be set up separately -- it's not part of the base system.

Alternative: Use /chef or /batch instead (uses native execution, works out of the box).
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
python3 ~/.opencode/scripts/crew_unified.py "$ARGUMENTS"

# Professional mode (retry logic, metrics):
python3 ~/.opencode/scripts/crew_unified.py "$ARGUMENTS" --mode=pro
```

### Step 4: VERIFY & REPORT

Check results and summarize for user.

---

## When to Use

### Use /crew when:
- Multi-file refactoring
- Feature implementation (3+ files)
- Complex changes requiring coordination

### Don't use /crew when:
- Simple single-file edits (use /chef)
- Quick bug fixes
- Just reading/analyzing code
- crew_unified.py is not installed
