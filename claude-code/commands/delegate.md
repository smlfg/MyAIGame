Delegate a coding task to OpenCode via MCP. This command uses the structured MCP protocol — NOT shell subprocess calls.

**MANDATORY: Gather context BEFORE delegating.**

## Task: $ARGUMENTS

## Steps:

1. **Understand the task**: Read the user's request above.

2. **Assess complexity**:
   - **SIMPLE** (1 file, clear task) → use `opencode_ask` (one-shot)
   - **COMPLEX** (multiple files, architecture decisions) → use session workflow

3. **Gather context**: Before sending anything to OpenCode, YOU must:
   - Read the relevant files that will be modified
   - Understand the codebase structure (run /snapshot if needed)
   - Identify dependencies and potential conflicts
   - Formulate a clear, specific task description

4. **Formulate the delegation prompt**: Write a clear prompt that includes:
   - What needs to be done (specific, not vague)
   - Which files to modify
   - What patterns/conventions to follow (from the existing code)
   - What NOT to do (common mistakes to avoid)

5. **Delegate via MCP**:

   ### Simple tasks → One-shot:
   ```
   opencode_ask(prompt="...", directory="/path/to/project")
   ```

   ### Complex tasks → Session workflow:
   ```
   opencode_session_create(title="...")
   opencode_message_send(sessionId="...", prompt="Step 1: ...")
   opencode_review_changes(sessionId="...")  → check what changed
   opencode_reply(sessionId="...", prompt="Step 2: ...")
   ```

   ### If something goes wrong:
   ```
   opencode_session_revert(sessionId="...", messageId="...")  → undo last change
   opencode_session_fork(sessionId="...", title="Alternative approach")  → try different approach
   ```

6. **Verify the result**: After OpenCode responds:
   - Use `opencode_review_changes` or read files directly to check changes
   - Run any relevant tests
   - Check for regressions
   - Report back to the user

**IMPORTANT**: Always set the `directory` parameter to the current project path.

## Fallback:
If the OpenCode MCP server is not responding within 60 seconds, do the task directly instead of waiting. Tell the user: "OpenCode MCP not responding — handling this directly."

## Anti-patterns:
- NEVER delegate without gathering context first
- NEVER send vague one-liners ("fix the bug") — be specific
- NEVER skip verification of the result
- NEVER forget the `directory` parameter
