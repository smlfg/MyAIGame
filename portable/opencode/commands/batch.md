---
name: batch
description: "Execute multiple tasks in one pass -- efficient batching"
argument-hint: "[task 1] | [task 2] | [task 3] ..."
---

# /batch -- Multi-Task Execution

Execute multiple tasks in a single focused pass. Efficient because context is gathered once.

**Tasks:** $ARGUMENTS

## Steps

1. **Parse Tasks** from `$ARGUMENTS`:
   - Separators: `|` or numbered list (1. 2. 3.) or bullet list (- item)
   - Max 10 tasks per batch

2. **Gather context once** (not per task!):
   Run `bash ~/.opencode/hooks/gather-context-enhanced.sh "$(pwd)" "$ARGUMENTS"` and capture as CONTEXT.

3. **Execute all tasks sequentially:**
   - Use CONTEXT as your guide
   - Handle dependencies (if task B needs result of A, do A first)
   - Report per task: what was done, which files changed

4. **Final Report:**
   - Which tasks completed
   - Which files changed
   - Blockers or open points

## Rules
- Independent tasks: execute sequentially in one pass
- Dependent tasks (B needs A): respect ordering
- Context is gathered ONCE, not per task
- Max 10 tasks per batch -- split if more
