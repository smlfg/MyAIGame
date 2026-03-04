# Hook & Config Compatibility Matrix

What works where across Claude Code, Codex CLI, and OpenCode.

## Hooks

| Hook Script | Purpose | Claude Code | Codex CLI | OpenCode |
|---|---|---|---|---|
| `gather-context.sh` | Inject project context (git, stack, structure) | Native hook (PreToolUse) | Manual/instructions.md | Plugin: `context-injection.ts` |
| `gather-context-enhanced.sh` | Extended context with keyword auto-detection | Native hook | Manual only | Plugin: `context-injection.ts` |
| `syntax_check.py` | py_compile after file edits | Native hook (PostToolUse, Edit/Write) | Git pre-commit hook | Plugin: `post-response.ts` |
| `pre_commit_tests.py` | Run pytest before git commit | Native hook (PreToolUse, Bash) | Git pre-commit hook | Plugin: `pre-commit.ts` |
| `post_tool_use.py` | Send tool results to voice daemon (MultiKanalAgent) | Native hook (PostToolUse) | Wrapper script needed | Plugin: `post-response.ts` |
| `stop.py` | Send final response to voice daemon | Native hook (Stop) | Wrapper script needed | Not portable (no Stop event) |
| `session-extract.sh` | Extract messages from session JSONL | Utility (manual) | Not applicable | Not applicable |
| `codex_advisor.py` | Second opinion from Codex on errors | Native hook (PostToolUse/Failure) | Native (IS Codex) | Plugin: `on-error.ts` (no AI call) |
| `codex_session_review.py` | Session-wide error pattern analysis | Native hook (Stop) | Native (IS Codex) | Plugin: `on-error.ts` (threshold alert) |

## Portability Legend

| Symbol | Meaning |
|---|---|
| Native hook | Runs automatically via the tool's hook system |
| Plugin | Ported as OpenCode experimental plugin (.ts) |
| Git pre-commit hook | Works via standard git hooks, not tool-specific |
| Wrapper script | Needs external shell wrapper around the CLI |
| Manual only | Must be run manually or included in prompts |
| Not portable | Cannot be replicated on this platform |
| Not applicable | Concept does not exist on this platform |

## Config Mapping

| Setting | Claude Code (`settings.json`) | Codex (`config.toml`) | OpenCode (`opencode.json`) |
|---|---|---|---|
| **Permissions** | `permissions.allow[]` (granular per-tool) | `approval_policy` (suggest/auto-edit/full-auto) | `permission` (ask/auto-edit/allow) |
| **MCP Servers** | `mcpServers{}` (5 servers defined) | Not supported | `mcp{}` (3 servers — no gemini, no opencode) |
| **Hooks** | `hooks{}` (PreToolUse, PostToolUse, Stop, etc.) | Not supported (use git hooks) | `experimental.hooks{}` (limited, experimental) |
| **Model Selection** | Via CLI flag or env | `model = "o4-mini"` | `model.default{}` + `model.fast{}` |
| **Sandbox** | No sandbox (trusts permissions) | `sandbox = true` (network-disabled) | No sandbox |
| **Instructions** | `.claude/CLAUDE.md` | `.codex/instructions.md` | `.opencode/instructions.md` or `AGENTS.md` |

## MCP Server Portability

| MCP Server | Claude Code | Codex CLI | OpenCode |
|---|---|---|---|
| `opencode` (opencode-mcp) | Yes | No (no MCP support) | N/A (would be recursive) |
| `gemini` (gemini-mcp-tool) | Yes | No | Omitted (use built-in search) |
| `filesystem` (@modelcontextprotocol/server-filesystem) | Yes | No | Yes |
| `memory` (@modelcontextprotocol/server-memory) | Yes | No | Yes |
| `github` (github-mcp via wrapper) | Yes | No | Yes (direct npx) |

## What Cannot Be Ported

### To Codex CLI
- **All hooks** — Codex has no hook system. Only git hooks work for pre-commit.
- **MCP servers** — Codex does not support MCP. Tool access is via sandbox shell only.
- **Granular permissions** — Only 3 modes (suggest/auto-edit/full-auto), no per-tool control.
- **Voice/narration** — Requires external wrapper script around `codex` CLI.

### To OpenCode
- **Stop event hooks** — OpenCode has no session-end event. `stop.py` cannot be ported.
- **Codex second opinion** — Cannot call another AI from within OpenCode without MCP. The `on-error.ts` plugin provides error tracking but not AI analysis.
- **PreToolUse blocking** — OpenCode's experimental plugin API may not support blocking tool calls. `pre-commit.ts` is best-effort.
- **Async hooks** — Claude Code supports `async: true` for non-blocking hooks. OpenCode plugins run synchronously.

### From Codex-Specific Scripts
- `codex_advisor.py` and `codex_session_review.py` are already Codex-specific integrations designed to be called FROM Claude Code. They don't need porting — they ARE the cross-tool integration.

## File Locations

```
portable/
  hooks/                          # Shared scripts (bash + python, universal)
    gather-context.sh             # Project context collector
    gather-context-enhanced.sh    # Extended context with keyword detection
    syntax_check.py               # Python syntax checker
    pre_commit_tests.py           # Pre-commit test runner
    post_tool_use.py              # Voice narration (MultiKanalAgent)
    stop.py                       # Session-end narration
    session-extract.sh            # Session JSONL parser
    codex_advisor.py              # Codex second opinion (Codex-specific)
    codex_session_review.py       # Codex session review (Codex-specific)
    hooks.json                    # Claude Code hook definitions (reference)
  codex/
    config.toml                   # Codex CLI configuration
  opencode/
    opencode.json                 # OpenCode configuration
    plugins/
      context-injection.ts        # gather-context.sh equivalent
      post-response.ts            # post_tool_use.py + syntax_check.py equivalent
      on-error.ts                 # codex_advisor.py equivalent (without AI call)
      pre-commit.ts               # pre_commit_tests.py equivalent
```

## Deployment Notes

1. **Claude Code**: Copy `hooks/` to project's `.claude/hooks/`, use `settings.json` as-is.
2. **Codex CLI**: Copy `config.toml` to `~/.codex/config.toml`. For pre-commit tests, install `pre_commit_tests.py` as `.git/hooks/pre-commit`. Voice hooks require a wrapper script.
3. **OpenCode**: Copy `opencode.json` to project root. Copy `plugins/` alongside it. Plugin API is experimental — verify compatibility with your OpenCode version.
