---
name: auto
description: "Smart auto-routing -- picks the best execution method automatically"
argument-hint: "[task description]"
---

# /auto -- Smart Auto-Routing

Analyze the task and choose the optimal execution method. Never ask the user which method.

**Task:** $ARGUMENTS

## Routing Logic (check in order)

1. Task is a question ("?" at end, "was ist", "wie funktioniert", "explain", "what is") -> answer directly, NO delegation
2. Task contains "test", "coverage", "pytest" -> /test pattern: run cascading test pipeline
3. Task contains "research", "suche", "best practice", "what's the best", "compare" -> /research pattern: web search
4. Task contains "refactor", "multi-file", "rename everywhere", "3+ files" -> session workflow with context gathering
5. Task is a small fix (1-2 files, clearly scoped) -> execute directly (chef-lite pattern)
6. Everything else -> context-enhanced execution (chef pattern): `gather-context-enhanced.sh` + execute

## Execution

Execute the chosen method immediately -- no further questions.

For chef pattern:
1. Run `bash ~/.opencode/hooks/gather-context-enhanced.sh "$(pwd)" "$ARGUMENTS"` -> CONTEXT
2. Execute the task using CONTEXT

For chef-lite pattern:
1. Execute the task directly

## Report

1 sentence after completion: "Used [method] -- [what was done, which file]"
