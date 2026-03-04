---
name: check-state
description: "Check current project state before making any changes"
category: utility
cost-tier: free
dependencies:
  tools: [shell, file_read]
tags: [utility, safety, pre-check]
---

# /check-state -- Pre-Change State Check

Before making ANY changes, perform these checks and report findings:

1. {{shell("pwd")}} -- confirm working directory
2. {{shell("ls -la")}} -- see current files and folder structure
3. {{shell("tree -L 2 --dirsfirst")}} -- visual overview (if tree is available)
4. {{shell("git status && git branch -a")}} -- git state (if inside a git repo)
5. Check for existing config files, READMEs, or project manifests (package.json, setup.py, pyproject.toml, Makefile)
6. Summarize what exists BEFORE proposing any changes
7. {{ask_user("Does my understanding match your expectations?")}} -- confirm before proceeding

Do NOT skip any of these steps. Do NOT start writing code or making changes until the user confirms.
