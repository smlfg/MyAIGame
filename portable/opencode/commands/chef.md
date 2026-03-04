---
name: chef
description: "Context-enhanced coding task execution (native in OpenCode)"
argument-hint: "[task description]"
---

# /chef -- Execute coding task with project context

You are in **Execution Mode**. This is a native OpenCode command -- no delegation needed because YOU are the execution engine.

**Task:** $ARGUMENTS

## Process

1. **Gather context** (zero LLM tokens):
   Run `bash ~/.opencode/hooks/gather-context-enhanced.sh "$(pwd)" "$ARGUMENTS"` and capture output as CONTEXT.

2. **Execute the task directly** using CONTEXT as your guide:
   - Follow existing code patterns in this project
   - One task, one change, keep it focused
   - Add tests where appropriate

3. **Report** (2-3 sentences max):
   - What was done
   - Files modified
   - Any blockers or next steps

## Rules
- ALWAYS gather context first via the script
- One task, one focused change
- Follow existing patterns
- Report concisely when done
