Git branch setup workflow. Follow these steps exactly:

1. Run `git status` to check for uncommitted changes
2. Run `git branch -a` to list ALL existing branches (local and remote)
3. Run `git log --oneline --graph --all | head -30` to visualize branch structure
4. Present a clear summary of what currently exists:
   - Which branches exist
   - What each branch contains (check key files per branch)
   - What the current branch is

5. Ask the user: "What branches do you want to create and what should each contain?"

6. After the user confirms the plan:
   - Create ALL new branches independently from main/master (NOT chained from each other)
   - For each branch: `git checkout main && git checkout -b <branch-name>`
   - Verify each branch with `git log --oneline -3` after creation

7. After all branches are created, run `git branch -a` and `git log --oneline --graph --all | head -40` to show the final result

IMPORTANT: Never create chained/nested branches unless the user explicitly asks for it. Every new branch starts from main.
