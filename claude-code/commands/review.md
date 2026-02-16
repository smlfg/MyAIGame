Perform a thorough code review of the current changes or specified files.

## Target: $ARGUMENTS

## Steps:

1. **Identify what to review**:
   - If no specific files given: review all uncommitted changes (`git diff` and `git diff --staged`)
   - If files specified: review those files
   - If a PR number given: fetch and review that PR

2. **Run automated checks first**:
   - Check for syntax errors (python -m py_compile for .py files)
   - Check for common issues (unused imports, undefined variables)
   - Look for hardcoded secrets or credentials

3. **Manual review — check for these categories**:

   ### Security
   - [ ] No hardcoded secrets, tokens, or passwords
   - [ ] Input validation on user-facing boundaries
   - [ ] No SQL injection, XSS, or command injection vectors
   - [ ] Proper error handling (no stack traces leaked to users)

   ### Quality
   - [ ] Code follows existing project conventions
   - [ ] No unnecessary complexity or over-engineering
   - [ ] Functions are focused (single responsibility)
   - [ ] Variable names are clear and descriptive

   ### Maintainability
   - [ ] Changes are well-scoped (not mixing unrelated changes)
   - [ ] No dead code or commented-out blocks
   - [ ] Edge cases considered
   - [ ] Error messages are helpful

   ### Performance
   - [ ] No obvious N+1 queries or unnecessary loops
   - [ ] No blocking operations in async code
   - [ ] Large files or datasets handled efficiently

4. **Report findings**:
   - List issues by severity: CRITICAL > WARNING > SUGGESTION
   - For each issue: file, line, what's wrong, how to fix it
   - End with an overall assessment: APPROVE / NEEDS CHANGES / BLOCK

## Output format:
```
## Code Review: [scope]

### CRITICAL (must fix)
- file.py:42 — SQL injection vulnerability in user query

### WARNING (should fix)
- utils.py:15 — Unused import 'os'

### SUGGESTION (nice to have)
- main.py:88 — Could extract this into a helper function

### Overall: NEEDS CHANGES
Summary of findings...
```
