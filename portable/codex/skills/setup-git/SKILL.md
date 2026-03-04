---
name: setup-git
description: "Git branch setup workflow -- visualize, plan, create branches"
category: utility
cost-tier: free
dependencies:
  tools: [shell]
tags: [git, branching, setup]
---

# /setup-git -- Git Branch Setup

Git branch setup workflow. Follow these steps exactly:

1. {{shell("git status")}} -- check for uncommitted changes
2. {{shell("git branch -a")}} -- list ALL existing branches
3. {{shell("git log --oneline --graph --all | head -30")}} -- visualize branch structure
4. Present a clear summary:
   - Which branches exist
   - What each branch contains
   - What the current branch is

5. {{ask_user("What branches do you want to create and what should each contain?")}}

6. After the user confirms the plan:
   - Create ALL new branches independently from main/master (NOT chained)
   - For each branch: `git checkout main && git checkout -b <branch-name>`
   - Verify each branch after creation

7. Show final result: {{shell("git branch -a && git log --oneline --graph --all | head -40")}}

**IMPORTANT:** Never create chained/nested branches unless the user explicitly asks for it. Every new branch starts from main.
