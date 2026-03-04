# TUI & Agent Architecture Research

> Research into existing AI coding agent TUIs and their architectures.
> Focus: architecture decisions we can steal for a unified TUI.
> Date: 2026-02-26

---

## 1. OpenCode (Go/TypeScript, Bubble Tea -> OpenTUI)

**Repo:** https://github.com/opencode-ai/opencode
**Deep Dive:** https://cefboud.com/posts/coding-agents-internals-opencode-deepdive/

### Architecture

Client/server split -- this is the most important design decision:

```
┌──────────────┐     HTTP/SSE      ┌──────────────────┐
│   TUI (Go)   │ <===============> │  Server (Bun/JS) │
│  or Desktop  │                   │   Hono HTTP API  │
│  or Web App  │                   │   AI SDK core    │
└──────────────┘                   └──────────────────┘
```

- **Server** runs on Bun runtime with Hono HTTP framework
- **TUI** was originally Go + Bubble Tea, now migrated to **OpenTUI** (TypeScript-based TUI framework, in-house)
- `opencode` command launches BOTH server + TUI as child processes
- TUI reads `OPENCODE_SERVER` env var to find the HTTP endpoint
- All AI orchestration is server-side; TUI is a thin display client
- SDK generated via Stainless for type-safe client code

### Provider Abstraction

Uses **Vercel AI SDK** -- single standardized function call interface:
- `streamText()` works identically for Anthropic, OpenAI, Gemini, etc.
- Each provider gets provider-specific system prompts (stored separately)
- Model instantiation requires `providerID` + `modelID`
- Tool definitions are provider-agnostic

### The Agent Loop ("The $1 Trillion Loop")

1. User prompt -> HTTP POST to server
2. Server prepares: context, history, tools, provider-specific prompts
3. `streamText()` calls LLM with tool list
4. Model responds with text + tool calls
5. Tools execute in Bun runtime
6. Results feed back to model (multi-step iteration)
7. All events stream via SSE to clients in real-time
8. Loop terminates when model stops calling tools or `stopWhen` fires (e.g., 1000 steps)

### Skills/Commands

- Tools defined with Zod schemas (name, description, input schema)
- Tools restricted per agent -- e.g., Plan agent cannot call `edit`
- MCP tools route through MCP clients instead of direct execution
- No formal "skill" or "slash command" system like Claude Code

### Streaming & Display

- **SSE (Server-Sent Events)** for real-time streaming to all clients
- Global **Event Bus** coordinates across application
- Events persist as message parts to disk
- Multiple clients can observe the same session simultaneously

### Session Management

- Conversation history with structured message parts (text, tool calls, results, errors)
- Per-session todo state in global map
- Git-backed snapshots for working state
- Auto-summarization when context exceeds ~90% of limit

### What We Can Steal

1. **Client/server split** -- decouple UI from AI logic, enable multiple frontends
2. **SSE event streaming** -- real-time updates to any number of clients
3. **Event Bus pattern** -- tools emit events, UI subscribes
4. **Auto-summarization** at 90% context -- we do this at ~30min, but percentage-based is smarter
5. **Agent-specific tool restrictions** -- Plan agent can't edit, etc.

---

## 2. Aider (Python, Terminal)

**Repo:** https://github.com/Aider-AI/aider
**Deep Dive:** https://deepwiki.com/Aider-AI/aider

### Architecture

Monolithic Python application with clean class hierarchy:

```
main.py
├── Coder (base_coder.py)     # Central orchestrator
│   ├── EditBlockCoder         # SEARCH/REPLACE blocks
│   ├── WholeFileCoder         # Complete file replacement
│   ├── UdiffCoder             # Unified diff format
│   ├── ContextCoder           # File selection + reflection
│   └── ArchitectCoder         # Two-model workflow
├── Model (models.py)          # LLM abstraction via LiteLLM
├── Commands (commands.py)     # /slash command processing
├── IO (io.py)                 # Terminal interaction
├── RepoMap (repomap.py)       # Codebase analysis
└── Repo (repo.py)             # Git integration
```

### Provider Abstraction

Uses **LiteLLM** -- the de facto Python LLM abstraction layer:
- Maps short aliases ("sonnet") to full identifiers ("anthropic/claude-sonnet-4-20250514")
- Three-tier model hierarchy:
  - `main_model`: Primary conversational AI
  - `weak_model`: Cheap model for commits and summaries
  - `editor_model`: Used in architect mode for implementation
- Configuration from `model-settings.yml` (behavioral) + `model-metadata.json` (technical specs)
- Token counting and cost tracking built into Model class

### The Architect/Editor Pattern

This is Aider's most innovative architecture decision:

```
User Request
    │
    ▼
┌──────────────┐     plan      ┌──────────────┐
│  Architect   │ ────────────> │    Editor     │
│  (smart,     │               │  (fast,       │
│   expensive) │               │   cheap)      │
│              │               │              │
│  "How to     │               │  Applies     │
│   solve it"  │               │  SEARCH/     │
│              │               │  REPLACE     │
└──────────────┘               └──────────────┘
```

Separates reasoning from editing:
1. Architect model analyzes requirements, creates implementation plan
2. Editor model executes the plan by applying code edits
3. Optimizes: use expensive model for thinking, cheap model for typing

**This maps exactly to our Strategy/Execution tier split.**

### Edit Formats

Different models work better with different edit formats:
- **whole**: Return entire file (simplest, most tokens)
- **diff**: SEARCH/REPLACE blocks (efficient, requires precision)
- **diff-fenced**: Variant for Gemini models
- **udiff**: Simplified unified diff (most efficient)

The `Coder.create(edit_format=...)` factory dispatches to the right subclass.

### Repo Map

Codebase-aware context using tree-sitter parsing:
- Extracts code structure across 100+ languages
- **PageRank algorithm** ranks symbols by relevance
- Weighting: mentioned identifiers get 10x boost, private identifiers get /10 penalty
- Dynamically generates context that fits within token budget

### Commands

Built-in `/slash` commands in `commands.py`:
- `/add`, `/drop`, `/run`, `/test`, `/commit`, `/undo`, etc.
- No plugin system -- commands are hardcoded
- Each command is a method on the Commands class

### What We Can Steal

1. **Architect/Editor split** -- mirrors our Strategy/Execution tiers perfectly
2. **Edit format abstraction** -- different models need different edit formats, this is elegant
3. **LiteLLM for Python provider abstraction** -- proven at scale, 100+ providers
4. **RepoMap with PageRank** -- smart context selection based on code structure, not just file names
5. **Three-tier model hierarchy** (main/weak/editor) -- we have four tiers, similar thinking
6. **Coder factory pattern** -- `Coder.create(edit_format=...)` dispatches to right implementation

---

## 3. Cursor & Windsurf (GUI Editors)

**Comparison:** https://www.builder.io/blog/windsurf-vs-cursor

### Cursor Architecture

VS Code fork with AI layer:
- **Agent Mode**: Full autonomous agent that reads files, runs commands, edits code
- **Edit Mode**: Targeted edits on selected code
- **Chat Panel**: Right-side tab, always available
- **Inline diffs**: Always shown -- philosophy of "you should always be reviewing code"
- **Intelligence touchpoints**: AI buttons appear contextually throughout the editor
- **Multi-model**: Supports Claude, GPT, Gemini, custom models
- **Context**: Uses `.cursorrules` file (project-level instructions, analogous to CLAUDE.md)

### Windsurf Architecture

Also VS Code fork, different philosophy:
- **Always-agentic**: Chat mode is agentic by default, no mode switching
- **Cascade**: Their agent system that indexes and pulls relevant code as needed
- **Hidden diffs**: Changes hidden by default, click "Open Diff" to see them
- **Write-to-disk**: AI writes changes to disk BEFORE approval -- see results in dev server in real-time
- **Minimalist UI**: Conceals implementation details behind expandable panels
- **Context**: Uses `.windsurfrules` file

### Key UX Pattern Differences

| Pattern | Cursor | Windsurf |
|---------|--------|----------|
| Diff display | Always inline, prominent | Hidden by default, expandable |
| Agent mode | Explicit mode selection | Always-on agentic |
| Approval | Review before apply | Write first, approve/reject after |
| Code context | Manual add + AI suggestions | Auto-indexed by Cascade |
| Philosophy | "Review everything" | "Trust the agent" |

### What We Can Steal

1. **Write-to-disk-first** (Windsurf) -- show results before approval, useful for TUI preview panels
2. **Intelligence touchpoints** (Cursor) -- contextual AI actions at relevant code locations
3. **Project-level instruction files** -- `.cursorrules` / `.windsurfrules` = our `AGENTS.md`
4. **Mode separation** -- Agent mode (autonomous) vs Edit mode (targeted) is a good UX split
5. **Auto-indexing** (Cascade) -- proactive codebase analysis, not just on-demand repo maps

---

## 4. goose (by Block, Rust)

**Repo:** https://github.com/block/goose
**Architecture docs:** https://block.github.io/goose/docs/goose-architecture/

### Architecture

Rust-based agent framework with CLI + Electron desktop:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  CLI / GUI  │ ──> │    Agent     │ ──> │  Extensions  │
│  (frontend) │     │  (core loop) │     │  (MCP-based) │
└─────────────┘     └──────────────┘     └──────────────┘
                          │
                          ▼
                    ┌──────────────┐
                    │   Provider   │
                    │  (any LLM)  │
                    └──────────────┘
```

### Provider Abstraction

- Provider trait in `providers/base.rs`
- 25+ LLM providers supported
- Provider-agnostic tool definitions

### Extension System (the standout feature)

goose's extension system is its architectural crown jewel. Six extension types:

| Type | Transport | Lifecycle | Example |
|------|-----------|-----------|---------|
| **Stdio** | stdin/stdout pipes | Child process | npx, uvx, local binaries |
| **StreamableHttp** | HTTP + SSE | Network server | Remote MCP servers |
| **Builtin** | In-memory function calls | Compiled-in | developer, computer |
| **Platform** | Direct Rust API | In-process | todo, skills, chat_recall |
| **InlinePython** | Ephemeral uvx | Spawned per-use | Dynamic Python scripts |
| **Frontend** | Client-side | UI-managed | clipboard, camera |

**Tool namespacing:** All tools get `{extension_name}__` prefix (e.g., `developer__write_file`). Prevents collisions, enables routing.

**Tool dispatch:**
1. Extract prefix from tool name
2. Locate extension in `ExtensionManager` HashMap
3. Strip prefix
4. Invoke via MCP client

**Configuration:** `~/.config/goose/config.yaml` for global, session-specific for per-session.

### The Agent Loop

1. Human request
2. Provider receives request + available tools list
3. LLM generates tool calls; goose executes them
4. Results returned to model
5. **Context revision** for token optimization (this is interesting -- active context management)
6. Final response

### AGENTS.md

goose was one of the first to adopt AGENTS.md (the OpenAI standard for project-level agent instructions). Now part of the Linux Foundation's Agentic AI Foundation (AAIF) alongside MCP.

### What We Can Steal

1. **Six extension types** -- brilliant taxonomy. Our hooks/plugins/MCP could use this classification
2. **Tool namespacing** (`extension__tool`) -- prevents collisions across extensions
3. **MCP as universal extension protocol** -- every extension speaks MCP regardless of transport
4. **Context revision** in the agent loop -- proactive token optimization, not just summarize-when-full
5. **Rust for core, plugins for everything else** -- performance where it matters, flexibility everywhere
6. **AGENTS.md adoption** -- validates our AGENTS.md approach, it's becoming an industry standard

---

## 5. Mentat (Python, Textual TUI)

**Repo:** https://github.com/AbanteAI/mentat

### Architecture

Python-based with Textual TUI framework:
- Terminal UI using **Textual** (rich Python TUI library)
- RAG-based auto-context (retrieval-augmented generation for file selection)
- Direct Git integration for tracking changes
- Multi-file coordinate edits

### Key Design Decisions

- **Auto Context via RAG**: Uses retrieval-augmented generation to automatically select relevant code snippets based on user query. Unlike Aider's tree-sitter + PageRank approach, Mentat uses embedding-based retrieval.
- **Textual TUI**: Rich terminal widgets, mouse support, scrollable panels -- more GUI-like than raw terminal
- **Multi-location edits**: Can coordinate changes across multiple files and locations in a single operation

### What We Can Steal

1. **RAG for auto-context** -- alternative to Aider's PageRank approach, worth testing both
2. **Textual for Python TUI** -- if we build a Python frontend, Textual is more polished than curses

---

## 6. Other Notable Projects

### Conduit (Multi-Agent TUI)

**Site:** https://getconduit.sh/

The closest thing to what we're building:
- **Tab-based** session management (up to 10 concurrent)
- Runs **Claude Code, Codex CLI, and Gemini CLI** side-by-side
- Real-time streaming display
- Token tracking with cost estimates
- Session persistence for resuming work
- OpenCode support coming soon

**Architecture insight:** Conduit doesn't abstract the agents -- it manages them as separate processes. Each tab is a different agent with its own stdin/stdout. This is simpler but limits cross-agent coordination.

### pi-agent (oh-my-pi)

**Repo:** https://github.com/can1357/oh-my-pi

Interesting technical choices:
- **Unified LLM API** with multi-provider support (Anthropic, OpenAI, Google, xAI, Groq, Cerebras, OpenRouter, any OpenAI-compatible endpoint)
- Streaming, tool calling, thinking/reasoning support
- **Cross-provider context handoffs** -- switch models mid-conversation
- Token and cost tracking
- **pi-tui**: Minimal TUI framework with differential rendering, flicker-free updates
- Hash-anchored edits, LSP integration, subagents

### Claude Squad

Manages multiple Claude Code sessions in parallel from a single terminal. Similar to Conduit but Claude-focused.

---

## 7. Synthesis: Architecture Patterns We Should Steal

### Pattern 1: Client/Server Split (OpenCode)

**Adopt.** Decouple AI logic from UI. Enables TUI, desktop, web, and mobile frontends from one backend. SSE for real-time streaming.

### Pattern 2: Architect/Editor Model Split (Aider)

**Already have this.** Our Strategy/Execution tier is the same idea. Aider validates that this pattern works at scale.

### Pattern 3: MCP as Universal Extension Protocol (goose)

**Adopt.** goose proves MCP works as THE extension protocol. Six transport types cover every integration scenario. Tool namespacing prevents collisions.

### Pattern 4: Edit Format Abstraction (Aider)

**Consider.** Different models produce better output with different edit formats. A factory pattern (`Coder.create(edit_format=...)`) is elegant.

### Pattern 5: Write-to-Disk-First (Windsurf)

**Interesting.** Let the agent write changes, show preview in real-time, then approve/reject. More fluid than review-before-apply.

### Pattern 6: Context Revision Loop (goose)

**Adopt.** Active context management inside the agent loop, not just summarize-when-full. This is better than our "suggest /compact after 30min" approach.

### Pattern 7: Tab-Based Multi-Agent Sessions (Conduit)

**Adopt for TUI.** Run multiple agent backends in tabs. Each tab = different tool or session. Track costs per tab.

### Pattern 8: RepoMap with Relevance Ranking (Aider)

**Consider.** Tree-sitter + PageRank for smart context selection. Our `gather-context.sh` is simpler but less intelligent.

---

## 8. Provider Abstraction Comparison

| Tool | Abstraction Layer | Language | Providers | How It Works |
|------|------------------|----------|-----------|-------------|
| **OpenCode** | Vercel AI SDK | TypeScript | 75+ | Standardized function interface, provider-specific prompts |
| **Aider** | LiteLLM | Python | 100+ | Alias resolution, model metadata, cost tracking |
| **goose** | Custom Provider trait | Rust | 25+ | Trait-based polymorphism, config-driven |
| **Cursor** | Internal | TypeScript | ~10 | VS Code integration, model picker UI |
| **Conduit** | None (process mgmt) | Go | 3 agents | Each agent is a separate process |
| **pi-agent** | Custom unified API | TypeScript | 8+ | Cross-provider context handoffs |

**Recommendation for our unified TUI:**
- If TypeScript: **Vercel AI SDK** (proven, OpenCode uses it)
- If Python: **LiteLLM** (proven, Aider uses it)
- If Rust/Go: Custom **Provider trait** (goose's approach)

---

## 9. Skill/Command System Comparison

| Tool | System | Extensible? | Format |
|------|--------|-------------|--------|
| **Claude Code** | `/slash` commands | Yes (md files) | Markdown in `~/.claude/commands/` |
| **Codex CLI** | Skills | Yes (directories) | `~/.codex/skills/<name>/SKILL.md` |
| **OpenCode** | Tool definitions | Via MCP only | Zod schemas in code |
| **Aider** | `/commands` | No (hardcoded) | Python methods on Commands class |
| **goose** | Extensions (MCP) | Yes (MCP servers) | MCP protocol, any language |
| **Cursor** | `.cursorrules` | Partial (rules only) | Markdown rules file |

**Our approach** (universal SKILL.md with frontmatter + abstract tool syntax) is more structured than any of these. Closest to goose's MCP-based extensibility but with a simpler authoring format.

---

## 10. Key Takeaways for Our Unified TUI

1. **Client/server is non-negotiable.** Every serious tool is going this direction (OpenCode, goose). Enables multi-frontend.

2. **SSE for streaming.** Not WebSockets. SSE is simpler, HTTP-native, and every tool that streams uses it.

3. **MCP is winning.** goose built on it, OpenCode supports it, it's now in the Linux Foundation. Our extension system should speak MCP.

4. **AGENTS.md is becoming standard.** OpenAI created it, goose adopted it, 60k+ repos use it. Our portable AGENTS.md approach is validated.

5. **The architect/editor split is proven.** Aider, Claude Code (us), and Cursor all independently arrived at "smart model plans, fast model executes."

6. **Edit format matters.** Different models need different edit formats. A factory pattern for this is worth implementing.

7. **Tab-based multi-session is the TUI UX.** Conduit proves users want multiple agents/sessions in one terminal. Tabs, not panes.

8. **Tool namespacing prevents chaos.** goose's `extension__tool` pattern is simple and effective for multi-extension environments.

---

## Sources

- [OpenCode GitHub](https://github.com/opencode-ai/opencode)
- [OpenCode Architecture Deep Dive](https://cefboud.com/posts/coding-agents-internals-opencode-deepdive/)
- [OpenCode Docs](https://opencode.ai/docs/)
- [Aider GitHub](https://github.com/Aider-AI/aider)
- [Aider Architecture (DeepWiki)](https://deepwiki.com/Aider-AI/aider)
- [Aider Edit Formats](https://aider.chat/docs/more/edit-formats.html)
- [Aider Architect Mode](https://aider.chat/2024/09/26/architect.html)
- [goose GitHub](https://github.com/block/goose)
- [goose Architecture Docs](https://block.github.io/goose/docs/goose-architecture/)
- [goose Extension Types (DeepWiki)](https://deepwiki.com/block/goose/5.3-extension-types-and-configuration)
- [Cursor vs Windsurf Comparison](https://www.builder.io/blog/windsurf-vs-cursor)
- [Conduit TUI](https://getconduit.sh/)
- [pi-agent (oh-my-pi)](https://github.com/can1357/oh-my-pi)
- [Mentat GitHub](https://github.com/AbanteAI/mentat)
- [AAIF Announcement (Linux Foundation)](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)
