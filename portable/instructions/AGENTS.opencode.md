# OpenCode-Specific Overrides

> These instructions supplement AGENTS.md for OpenCode environments.
> OpenCode reads this from: .opencode/AGENTS.md or project root AGENTS.md

---

## Environment Differences

OpenCode is a **local agent** with full system access:
- Full internet access (web research, API calls)
- MCP server connections available
- Background/async task execution supported
- Multiple provider backends configurable

## Delegation Architecture — OpenCode Mapping

| Universal Tier | OpenCode Equivalent |
|---------------|-------------------|
| Strategy Tier | The orchestrating agent (e.g., Claude Code calling OpenCode via MCP) |
| Execution Tier | OpenCode itself (`opencode_run`, `opencode_ask`) |
| Research Tier | Gemini MCP (`mcp__gemini__ask-gemini`) if available, else web search |
| Background Tier | `opencode_fire` + `opencode_check` for async tasks |

## Provider Configuration

Available providers (configure in auth.json):
- Use whichever provider has valid API keys configured
- **Known issue:** `providerID: "anthropic"` without an API key causes `"Unexpected end of JSON input"` -- this is an auth error, not a prompt size issue. Switch to a provider with valid credentials.

When calling OpenCode tools, ALWAYS specify `providerID` and `modelID`:
```
opencode_ask({
  prompt: "...",
  providerID: "<configured-provider>",
  modelID: "<configured-model>"
})
```

## Web Research

Research priority order:
1. `mcp__gemini__ask-gemini` (cheapest, if available)
2. Web search tool (fallback)
3. Own knowledge (with freshness caveat)

NEVER run web search and Gemini in parallel. Gemini FIRST.

## Skills Mapping

| Universal Skill | OpenCode Implementation |
|----------------|----------------------|
| chef | `gather-context.sh` -> `opencode_run` with context |
| chef-lite | `opencode_ask` (direct, no context gathering) |
| chef-async | `opencode_fire` + `opencode_check` |
| research | `mcp__gemini__ask-gemini` |
| test | `opencode_run` with test commands + auto-fix loop |
| check-state | Shell: `pwd && ls && git status` |
| checkpoint | Shell: `git add -A && git commit` + summary |

## Context Gathering

OpenCode supports context hooks:
- `gather-context.sh <directory> "<task>"` -- collects project structure, git status, relevant files
- Pass the output as context to `opencode_run` or `opencode_ask`
- This costs $0 (local shell only) and dramatically improves delegation quality

## Async Workflows

For long-running tasks:
```
1. opencode_fire({prompt: "..."})     -- starts task, returns immediately
2. opencode_check({sessionId: "..."}) -- check progress (cheap, read-only)
3. opencode_review_changes({...})     -- see diffs when done
```

**Important:** Always clean up async sessions. Check `opencode_sessions_overview` regularly.

## Anticipation (Parallel Work Detection)

When Samuel mentions parallel work:
- `opencode_sessions_overview` -- shows all active sessions
- `opencode_file_list` / `opencode_find_file` -- search across project
- `mcp__filesystem__directory_tree` on parent directories
- `git diff` + `git ls-files --others` in all repos

## File Paths

OpenCode configuration locations:
- Project-level: `.opencode/AGENTS.md` in project root
- Alternatively: `AGENTS.md` in project root
- Companion files: `companion/` directory relative to AGENTS.md
