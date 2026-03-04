---
name: delegate
description: "Smart task execution with complexity assessment"
argument-hint: "[task description]"
---

# /delegate -- Execute with complexity-aware approach

In OpenCode you ARE the execution engine. This command assesses complexity and picks the right approach.

**Task:** $ARGUMENTS

## Steps

1. **Understand the task**: Read the user's request.

2. **Assess complexity**:
   - **SIMPLE** (1 file, clear task) -> execute directly (like /chef-lite)
   - **COMPLEX** (multiple files, architecture decisions) -> gather context first, use session workflow

3. **Gather context** (for complex tasks):
   - Read relevant files that will be modified
   - Understand codebase structure
   - Identify dependencies and potential conflicts
   - Formulate a clear approach

4. **Execute**:
   ### Simple tasks:
   Make the change directly.

   ### Complex tasks:
   Work through it step by step, verifying each change.

5. **Verify the result**:
   - Run any relevant tests
   - Check for regressions
   - Report back to the user

## Rules
- NEVER execute without understanding the task first
- NEVER make vague changes -- be specific
- ALWAYS verify the result
- For complex tasks, gather context BEFORE executing

## Anti-patterns
- NEVER skip context gathering for complex tasks
- NEVER mix unrelated changes
- NEVER skip verification
