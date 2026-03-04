---
name: snapshot
description: "Generate a project snapshot of the current working directory"
category: utility
cost-tier: free
dependencies:
  tools: [shell]
  external: ["snapshot.py"]
tags: [utility, overview, project-scan]
---

# /snapshot -- Project Snapshot

Generate a project snapshot of the current working directory.

## Process

{{shell("python3 ~/.claude/scripts/snapshot.py")}}

After reviewing the output:
1. Summarize the key findings (main language, project type, notable configs)
2. Identify any potential issues (missing README, no tests, large untracked files)
3. {{ask_user("What would you like to focus on?")}}

## Codex Note
The `snapshot.py` script must exist at the expected path. If not available, fall back to manual inspection: `tree -L 2`, `git status`, check for config files.
