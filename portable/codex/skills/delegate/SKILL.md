---
name: delegate
description: "Full delegation with complexity assessment -- simple vs. session workflow"
argument-hint: "[task description]"
category: delegation
cost-tier: low
dependencies:
  tools: [delegate_code, delegate_code_run, delegate_code_session, file_read, review_changes, revert_session]
tags: [delegation, complexity-aware, structured]
---

# /delegate -- Full Delegation with Complexity Assessment

Delegate a coding task to the execution engine. Uses structured protocol for routing.

**MANDATORY: Gather context BEFORE delegating.**

## Task: $ARGUMENTS

## Steps:

1. **Understand the task**: Read the user's request above.

2. **Assess complexity**:
   - **SIMPLE** (1 file, clear task) -> use one-shot delegation: {{delegate_code(prompt, dir)}}
   - **COMPLEX** (multiple files, architecture decisions) -> use session workflow

3. **Gather context**: Before delegating, YOU must:
   - Read the relevant files that will be modified
   - Understand the codebase structure
   - Identify dependencies and potential conflicts
   - Formulate a clear, specific task description

4. **Formulate the delegation prompt**: Write a clear prompt that includes:
   - What needs to be done (specific, not vague)
   - Which files to modify
   - What patterns/conventions to follow (from the existing code)
   - What NOT to do (common mistakes to avoid)

5. **Delegate**:

   ### Simple tasks -> One-shot:
   {{delegate_code(prompt="detailed task description", dir=project_dir)}}

   ### Complex tasks -> Session workflow:
   {{delegate_code_session(title="Task description", dir=project_dir)}}
   Then send step-by-step messages to the session.
   Use {{review_changes(sessionId)}} to check changes.
   Use {{revert_session(sessionId)}} if something goes wrong.

6. **Verify the result**: After execution:
   - Review changes or read files directly to check
   - Run any relevant tests
   - Check for regressions
   - Report back to the user

## Fallback
If execution engine not responding within 60 seconds, do the task directly.
Tell user: "Execution engine not responding -- handling this directly."

## Anti-patterns
- NEVER delegate without gathering context first
- NEVER send vague one-liners ("fix the bug") -- be specific
- NEVER skip verification of the result
- NEVER forget the directory parameter
