# Unified Agent Coding TUI -- Architecture

> One terminal. Three backends. Thirty skills. Zero vendor lock-in.

**Codename:** `agentui` (working title -- Samuel picks the real name)

---

## 1. The Vision

Right now, switching between Claude Code, Codex CLI, and OpenCode means switching terminals, configs, mental models, and skills. That is like having three guitars -- each tuned differently, each requiring different picks, each with songs that only work on THAT guitar.

`agentui` is the universal amplifier. Plug in any guitar, play any song. The skills you wrote once (in `portable/SPEC.md` format) work everywhere. The TUI handles the translation.

```
┌───────────────────────────────────────────────────────┐
│                    agentui TUI                         │
│                                                        │
│  ┌─────────┐  ┌──────────────────────────┐  ┌──────┐ │
│  │ Session  │  │      Chat / Output       │  │Skills│ │
│  │ Sidebar  │  │                          │  │Panel │ │
│  │          │  │  > /chef fix the auth    │  │      │ │
│  │ s1: CC   │  │  Routing to: Claude Code │  │/chef │ │
│  │ s2: Cdx  │  │  Cost: ~$3 (Sonnet)     │  │/test │ │
│  │ s3: OC   │  │                          │  │/focus│ │
│  │          │  │  [streaming response...] │  │/auto │ │
│  │          │  │                          │  │ ...  │ │
│  ├─────────┤  ├──────────────────────────┤  │      │ │
│  │ Focus:   │  │ Input                    │  │      │ │
│  │ Auth bug │  │ > _                      │  │      │ │
│  │ 14/15min │  │                          │  │      │ │
│  └─────────┘  └──────────────────────────┘  └──────┘ │
│  [F1 Help] [F2 Sessions] [F3 Skills] [F4 Route] [F5] │
└───────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack Decision

### The Contenders

| Framework | Language | Pros | Cons | Used By |
|-----------|----------|------|------|---------|
| **Bubble Tea** | Go | Elm architecture, huge ecosystem (Lip Gloss, Glamour), async first | Samuel doesn't know Go, compilation required | OpenCode, Lazygit, Charm tools |
| **Ratatui** | Rust | Best performance, zero-cost abstractions, full control | Steepest learning curve, Samuel doesn't know Rust | gitui, bottom, many new TUI tools |
| **Textual** | Python | Samuel knows Python, CSS-like styling, web preview, rich widgets | Slower than Go/Rust, async complexity, less terminal-native | Trogon, posting, many dashboards |
| **Ink** | Node/TS | React mental model, JSX in terminal | Performance ceiling, heavy runtime, fewer real TUI apps | Pastel, some CLI tools |

### Recommendation: Python + Textual

**Why:**

1. **Samuel knows Python.** This is the single most important factor. A TUI you can maintain beats a TUI with 15% better rendering. Go and Rust have 6-12 month learning curves for non-trivial projects. Python is day-one productive.

2. **MCP SDK is mature in Python.** The official `mcp` Python SDK (v1.25.0, Jan 2026) is the most complete implementation. Since the entire system speaks MCP to backends, having first-class MCP support in the implementation language is critical.

3. **Textual is surprisingly capable.** 60 FPS rendering, CSS-like layouts, built-in widgets (DataTable, Tree, TextArea, TabbedContent, Markdown), mouse support, and the ability to run in a web browser as fallback. 250k+ PyPI downloads in Q1 2025.

4. **asyncio fits the architecture.** Multiple backends streaming simultaneously is naturally async. Python's asyncio + Textual's async-first design handles this without the ceremony of Go goroutines or Rust's tokio.

5. **Rapid iteration.** No compilation step. Edit, save, see changes. For a solo developer, this 10x multiplier matters more than a 2x performance gain.

**The tradeoff:** Textual is ~3-5x slower than Bubble Tea for rendering. For an AI coding agent where 95% of wall-clock time is waiting for API responses, this is irrelevant. The bottleneck is never the TUI -- it is the LLM.

**Escape hatch:** If performance ever becomes a real issue (it almost certainly will not), the Provider Abstraction Layer (Section 4) is language-agnostic. The backend communication happens over stdin/stdout/HTTP. You could rewrite the TUI in Go while keeping all the Python backend adapters.

### Dependencies

```
# Core
textual>=0.90.0       # TUI framework
mcp>=1.25.0           # MCP client SDK
httpx>=0.27.0         # Async HTTP for API calls
pydantic>=2.0         # Config and message schemas

# Backend adapters
anthropic>=0.40.0     # Claude API (direct, for routing without CLI)
openai>=1.50.0        # OpenAI API (for Codex backend)

# Optional
rich>=13.0            # Pretty printing outside TUI
pyyaml>=6.0           # YAML frontmatter parsing for skills
```

---

## 3. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         agentui                              │
│                                                              │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │   TUI Layer  │  │  Skill Engine │  │  Session Manager │  │
│  │  (Textual)   │  │               │  │                  │  │
│  │              │  │  Load SKILL.md│  │  Multi-session   │  │
│  │  Pages       │  │  Resolve tools│  │  History         │  │
│  │  Widgets     │  │  Pick backend │  │  Context carry   │  │
│  │  Key bindings│  │  Execute      │  │  Focus tracking  │  │
│  └──────┬───────┘  └──────┬────────┘  └────────┬─────────┘  │
│         │                 │                     │            │
│  ┌──────┴─────────────────┴─────────────────────┴─────────┐  │
│  │                   Router / Orchestrator                 │  │
│  │                                                        │  │
│  │  Cost optimizer   Capability matcher   Fallback chain  │  │
│  └────────┬──────────────┬──────────────────┬─────────────┘  │
│           │              │                  │                │
│  ┌────────┴────┐  ┌──────┴──────┐  ┌───────┴───────┐       │
│  │ Claude Code │  │  Codex CLI  │  │   OpenCode    │       │
│  │  Adapter    │  │  Adapter    │  │   Adapter     │       │
│  │             │  │             │  │               │       │
│  │ - MCP Client│  │ - CLI spawn │  │ - MCP Client  │       │
│  │ - API direct│  │ - API direct│  │ - API direct  │       │
│  │ - Streaming │  │ - Streaming │  │ - Streaming   │       │
│  └─────────────┘  └─────────────┘  └───────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility | Dependencies |
|-------|----------------|-------------|
| **TUI Layer** | Rendering, input handling, layout, themes | Textual |
| **Skill Engine** | Parse SKILL.md, resolve `{{tool()}}` abstractions, dispatch | pyyaml, SPEC.md format |
| **Session Manager** | Multi-session state, history, context, focus tracking | pydantic, sqlite |
| **Router** | Pick the right backend for each task | Config, cost tables, availability |
| **Adapters** | Translate abstract operations to backend-specific calls | MCP SDK, API clients |

---

## 4. Provider Abstraction Layer

The core interface that every backend implements. This is the contract between the TUI and the outside world.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional
from enum import Enum


class BackendID(Enum):
    CLAUDE_CODE = "claude-code"
    CODEX_CLI = "codex-cli"
    OPENCODE = "opencode"


@dataclass
class BackendCapabilities:
    """What this backend can do."""
    can_stream: bool = True
    can_spawn_subagents: bool = False
    can_use_mcp: bool = False
    can_sandbox: bool = False
    can_voice: bool = False
    has_native_hooks: bool = False
    max_context_tokens: int = 200_000
    cost_per_1m_input: float = 0.0
    cost_per_1m_output: float = 0.0


@dataclass
class ToolCall:
    """A resolved tool invocation."""
    tool_name: str          # e.g. "delegate_code", "research", "shell"
    params: dict            # Tool-specific parameters
    backend_hint: Optional[BackendID] = None  # Router may override


@dataclass
class AgentConfig:
    """Configuration for spawning a sub-agent."""
    model_tier: str         # "strategy", "execution", "research", "background"
    prompt: str
    context: Optional[str] = None
    background: bool = False
    timeout_seconds: int = 300


@dataclass
class StreamToken:
    """A single token in a streaming response."""
    text: str
    is_tool_call: bool = False
    tool_call: Optional[ToolCall] = None
    is_done: bool = False
    cost_so_far: float = 0.0


class BackendAdapter(ABC):
    """Abstract interface that all backends implement."""

    @property
    @abstractmethod
    def id(self) -> BackendID:
        """Which backend this is."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> BackendCapabilities:
        """What this backend supports."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Can we reach this backend right now?"""
        ...

    @abstractmethod
    async def send_prompt(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_instructions: Optional[str] = None,
    ) -> str:
        """Send a prompt and get a complete response."""
        ...

    @abstractmethod
    async def stream_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_instructions: Optional[str] = None,
    ) -> AsyncIterator[StreamToken]:
        """Send a prompt and stream the response token by token."""
        ...

    @abstractmethod
    async def execute_tool(
        self,
        tool: ToolCall,
    ) -> str:
        """Execute a tool call and return the result."""
        ...

    @abstractmethod
    async def spawn_agent(
        self,
        config: AgentConfig,
    ) -> str:
        """Spawn a sub-agent and return its handle/session ID."""
        ...

    @abstractmethod
    async def check_agent(
        self,
        agent_handle: str,
    ) -> dict:
        """Check the status of a spawned agent."""
        ...
```

### Adapter Implementations

#### Claude Code Adapter

```python
class ClaudeCodeAdapter(BackendAdapter):
    """
    Two modes:
    1. CLI mode: spawn `claude` process, communicate via stdin/stdout
    2. API mode: direct Anthropic API calls (cheaper, no CLI overhead)
    3. MCP mode: connect to Claude Code's MCP servers
    """

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            can_stream=True,
            can_spawn_subagents=True,   # Task tool
            can_use_mcp=True,           # 5 MCP servers
            can_sandbox=False,
            can_voice=True,             # VoiceMode MCP
            has_native_hooks=True,      # Pre/PostToolUse, Stop
            max_context_tokens=200_000,
            cost_per_1m_input=15.0,     # Opus
            cost_per_1m_output=75.0,
        )
```

#### Codex CLI Adapter

```python
class CodexAdapter(BackendAdapter):
    """
    Two modes:
    1. CLI mode: spawn `codex` process (has built-in sandbox)
    2. API mode: direct OpenAI API calls
    """

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            can_stream=True,
            can_spawn_subagents=False,
            can_use_mcp=False,          # Not yet supported
            can_sandbox=True,           # Network-disabled sandbox
            can_voice=False,
            has_native_hooks=False,
            max_context_tokens=200_000,
            cost_per_1m_input=1.10,     # o4-mini
            cost_per_1m_output=4.40,
        )
```

#### OpenCode Adapter

```python
class OpenCodeAdapter(BackendAdapter):
    """
    Two modes:
    1. MCP mode: connect to OpenCode's MCP server (richest feature set)
    2. API mode: direct API calls with OpenCode's provider config
    """

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            can_stream=True,
            can_spawn_subagents=True,   # Separate sessions
            can_use_mcp=True,           # Native MCP support
            can_sandbox=False,
            can_voice=False,
            has_native_hooks=True,      # Plugin system
            max_context_tokens=200_000,
            cost_per_1m_input=3.0,      # Sonnet default
            cost_per_1m_output=15.0,
        )
```

---

## 5. Smart Router

The Router decides which backend handles each request. It is the brain of the system.

```python
@dataclass
class RoutingDecision:
    backend: BackendID
    reason: str
    estimated_cost: float
    fallback: Optional[BackendID] = None


class Router:
    """
    Decides which backend handles each request.
    Three strategies, evaluated in order:
    """

    def __init__(self, adapters: dict[BackendID, BackendAdapter], config: RouterConfig):
        self.adapters = adapters
        self.config = config

    async def route(self, request: RoutingRequest) -> RoutingDecision:
        # 1. User override — always wins
        if request.force_backend:
            return RoutingDecision(
                backend=request.force_backend,
                reason="User forced backend",
                estimated_cost=self._estimate_cost(request, request.force_backend),
            )

        # 2. Capability requirement — filter by what's needed
        capable = self._filter_by_capability(request)

        # 3. Availability — filter by what's online
        available = await self._filter_by_availability(capable)

        if not available:
            raise NoBackendAvailable(f"No backend can handle: {request}")

        # 4. Cost optimization — pick cheapest that qualifies
        if self.config.strategy == "cost":
            return self._pick_cheapest(available, request)

        # 5. Quality optimization — pick best model
        if self.config.strategy == "quality":
            return self._pick_best(available, request)

        # 6. Balanced — use skill hints + cost tiers
        return self._pick_balanced(available, request)
```

### Routing Rules

| Task Type | Primary Backend | Reason | Fallback |
|-----------|----------------|--------|----------|
| **Research** (`/research`, `{{research()}}`) | Any (cheapest) | Research is commodity | Next cheapest |
| **Code generation** (`/chef`, `{{delegate_code()}}`) | Codex ($0.15) or OpenCode ($3) | Code quality vs cost tradeoff | Claude Code ($15) |
| **Multi-agent orchestration** (`/test-crew`, `/swarm`) | Claude Code or OpenCode | Need sub-agent spawning | Degrade to sequential |
| **ADHD workflow** (`/focus`, `/quickwin`) | Any (local preferred) | No API calls needed | All local |
| **Sandbox execution** | Codex | Only one with network-disabled sandbox | OpenCode (no sandbox) |
| **Voice mode** | Claude Code | Only one with VoiceMode MCP | Not available |

### Cost-Based Routing Example

```
User: /chef fix the authentication bug in login.py

Router thinking:
  1. Skill "chef" needs: delegate_code, shell
  2. Capable backends: claude-code, codex-cli, opencode
  3. All available: yes
  4. Cost estimates:
     - codex-cli:    ~$0.15 (o4-mini, 10k tokens estimated)
     - opencode:     ~$0.30 (Sonnet, 10k tokens)
     - claude-code:  ~$1.50 (Opus overhead + Sonnet delegation)
  5. Quality sufficient for all: yes (simple code fix)

  Decision: codex-cli ($0.15, reason: cheapest capable backend)
  Fallback: opencode (if Codex API is down)
```

---

## 6. Skill Engine

The Skill Engine is the bridge between `SPEC.md` format skills and backend execution.

```python
class SkillEngine:
    """
    Load → Parse → Resolve → Route → Execute
    """

    def __init__(self, skill_dirs: list[Path], router: Router):
        self.skills: dict[str, Skill] = {}
        self.router = router
        self._load_all(skill_dirs)

    def _load_all(self, dirs: list[Path]):
        """Load all SKILL.md files from universal format directories."""
        for d in dirs:
            for skill_path in d.glob("*/SKILL.md"):
                skill = self._parse(skill_path)
                self.skills[skill.name] = skill

    def _parse(self, path: Path) -> Skill:
        """Parse YAML frontmatter + markdown body."""
        text = path.read_text()
        frontmatter, body = self._split_frontmatter(text)
        return Skill(
            name=frontmatter["name"],
            description=frontmatter.get("description", ""),
            argument_hint=frontmatter.get("argument-hint", ""),
            category=frontmatter.get("category", "utility"),
            cost_tier=frontmatter.get("cost-tier", "variable"),
            dependencies=frontmatter.get("dependencies", {}),
            body=body,
            tool_calls=self._extract_tool_calls(body),
        )

    def _extract_tool_calls(self, body: str) -> list[str]:
        """Find all {{tool_name(...)}} references in the body."""
        import re
        return re.findall(r'\{\{(\w+)\(', body)

    async def execute(self, skill_name: str, arguments: str, context: str) -> AsyncIterator[StreamToken]:
        """Execute a skill with the given arguments."""
        skill = self.skills[skill_name]

        # Resolve $ARGUMENTS
        resolved_body = skill.body.replace("$ARGUMENTS", arguments)

        # Determine required capabilities from tool calls
        required_caps = self._tool_calls_to_capabilities(skill.tool_calls)

        # Route to best backend
        decision = await self.router.route(RoutingRequest(
            skill=skill,
            required_capabilities=required_caps,
            estimated_tokens=len(resolved_body.split()) * 2,
        ))

        # Execute via chosen backend
        adapter = self.router.adapters[decision.backend]
        async for token in adapter.stream_response(
            prompt=resolved_body,
            context=context,
            system_instructions=self._get_system_instructions(decision.backend),
        ):
            yield token
```

### Skill Lifecycle

```
1. User types: /chef fix the login bug
                  │
2. SkillEngine.execute("chef", "fix the login bug", project_context)
                  │
3. Load chef/SKILL.md from portable/skills/
                  │
4. Parse frontmatter → category: delegation, cost-tier: low
   Parse body → tool_calls: [delegate_code, shell]
                  │
5. Replace $ARGUMENTS → "fix the login bug"
                  │
6. Router.route(skill=chef, capabilities=[delegate_code, shell])
   → Decision: codex-cli (cheapest, capable)
                  │
7. CodexAdapter.stream_response(resolved_body, context)
   → Streaming tokens back to TUI
                  │
8. TUI renders tokens in real-time
```

---

## 7. TUI Layout (Textual)

### Page Architecture

```python
class AgentApp(textual.app.App):
    """The main application."""

    CSS = """
    #sidebar { width: 25; }
    #main { width: 1fr; }
    #skills-panel { width: 20; display: none; }  /* Toggle with F3 */
    #status-bar { height: 1; dock: bottom; }
    #focus-bar { height: 3; dock: bottom; }
    """

    BINDINGS = [
        Binding("f1", "help", "Help"),
        Binding("f2", "sessions", "Sessions"),
        Binding("f3", "toggle_skills", "Skills"),
        Binding("f4", "route_info", "Routing"),
        Binding("f5", "focus_mode", "Focus"),
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+1", "backend_claude", "Claude"),
        Binding("ctrl+2", "backend_codex", "Codex"),
        Binding("ctrl+3", "backend_opencode", "OpenCode"),
        Binding("ctrl+0", "backend_auto", "Auto Route"),
        Binding("escape", "cancel", "Cancel"),
    ]
```

### Panel Layout

```
┌─────────────────────────────────────────────────────────────┐
│ agentui v0.1.0 | Backend: Auto | Session: auth-fix | $0.45 │
├──────────┬──────────────────────────────────┬───────────────┤
│ Sessions │ Chat                             │ Context       │
│          │                                  │               │
│ > auth   │ You: /chef fix login.py auth     │ login.py      │
│   db-mig │                                  │ auth/         │
│   refact │ [Claude Code via Sonnet]         │ tests/        │
│          │ I'll fix the authentication...   │               │
│          │                                  │ Modified:     │
│          │ ```python                        │  login.py     │
│          │ def authenticate(user, pw):      │  +15 -3       │
│          │     # Fixed: was using ==        │               │
│          │     return verify(hash(pw))      │ Cost: $0.32   │
│          │ ```                              │               │
│          │                                  │ Route: CC     │
│          │ Done. Fixed timing-safe compare. │ Model: Sonnet │
├──────────┼──────────────────────────────────┤               │
│ Focus    │                                  │               │
│          │ > _                              │               │
│ Auth bug │                                  │               │
│ 12/15min │                                  │               │
│ [██████░]│                                  │               │
└──────────┴──────────────────────────────────┴───────────────┘
 F1 Help  F2 Sessions  F3 Skills  F4 Route  F5 Focus  ^N New
```

### Key UX Principles (Learned from Lazygit and K9s)

1. **Everything visible at once.** No nested menus. Panels show state at all times. Lazygit's biggest insight: reduce context switching to zero.

2. **Keyboard-first, mouse-supported.** Every action has a keybinding. Mouse clicks work for panel selection and scrolling. No mouse-required interactions.

3. **Progressive disclosure.** The default view is simple (chat + input). F-keys reveal panels. Expert users see routing, costs, context. Beginners see a chat window.

4. **Status line as information radiator.** The bottom bar always shows: current backend, session name, cumulative cost, focus mode timer.

5. **Color-coded backends.** Claude Code = purple, Codex = green, OpenCode = blue. Every response is tagged with its source color. You always know WHO answered.

6. **No blocking operations.** Everything is async. Long-running operations show a spinner in the status bar. The input is never locked (you can start typing the next command while waiting).

---

## 8. ADHD Workflow Integration

These are not just skills -- they are first-class TUI features.

### Focus Mode (F5)

```
┌─ Focus Mode ──────────────────────┐
│                                    │
│  Session Goal: Fix auth bug        │
│  Time: 12:34 / 15:00              │
│  [████████████░░░░]  83%          │
│                                    │
│  Completed:                        │
│  [x] Read login.py                 │
│  [x] Identify timing attack        │
│  [ ] Write fix                     │
│  [ ] Run tests                     │
│                                    │
│  Parked Ideas:                     │
│  - Refactor auth module later      │
│  - Add 2FA support                 │
│                                    │
│  [Enter] Add step  [P] Park idea   │
│  [Space] Toggle    [Esc] Close     │
└────────────────────────────────────┘
```

When Focus Mode is active:
- Every new prompt is checked against the session goal
- Off-topic requests get a gentle nudge: "That's not your focus. Park it? (P)"
- Timer is visible in the sidebar at all times
- After 15 minutes: celebration animation + checkpoint prompt

### Quick Win Launcher (Ctrl+Q)

```
┌─ Quick Wins ──────────────────────┐
│                                    │
│  Scanned project. Found 3 wins:   │
│                                    │
│  1. Fix TODO in auth.py:42  ~3min  │
│  2. Remove unused import    ~1min  │
│  3. Update README badge     ~2min  │
│                                    │
│  [1-3] Pick one  [A] All three    │
│  [R] Rescan      [Esc] Close      │
└────────────────────────────────────┘
```

### Checkpoint Integration (Ctrl+S)

Not just git commit. Visual progress:

```
Checkpoint! "Fix timing-safe auth comparison"
  3 files | +15 -3 lines | Session cost: $0.45
  ████████████░░░░ 4/6 steps done
  "Starke Session! 67% durch."
```

### Session Log (visible in sidebar)

```
Sessions:
  > auth-fix (CC)     $0.45  [FOCUS 12m]
    db-migration (Cdx) $0.15  [DONE]
    refactor (OC)      $1.20  [PAUSED]
    research (CC)      $0.10  [3 sources]
```

---

## 9. Data Model

### Session State (SQLite)

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    backend TEXT NOT NULL,          -- 'claude-code' | 'codex-cli' | 'opencode'
    status TEXT DEFAULT 'active',   -- 'active' | 'paused' | 'done'
    focus_goal TEXT,                -- NULL or focus mode goal
    focus_start TIMESTAMP,
    focus_duration_minutes INTEGER DEFAULT 15,
    total_cost REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id),
    role TEXT NOT NULL,              -- 'user' | 'assistant' | 'system' | 'tool'
    content TEXT NOT NULL,
    backend TEXT,                    -- Which backend answered
    model TEXT,                      -- Which model was used
    cost REAL DEFAULT 0.0,
    tool_calls TEXT,                 -- JSON of tool calls made
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id),
    git_hash TEXT,
    commit_message TEXT,
    files_changed INTEGER,
    lines_added INTEGER,
    lines_removed INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parked_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id),
    idea TEXT NOT NULL,
    status TEXT DEFAULT 'parked',    -- 'parked' | 'done' | 'dismissed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Config (YAML)

```yaml
# ~/.config/agentui/config.yaml

backends:
  claude-code:
    enabled: true
    mode: cli           # cli | api | mcp
    cli_path: ~/.local/bin/claude
    api_key: ${ANTHROPIC_API_KEY}
    default_model: claude-sonnet-4-5
    strategy_model: claude-opus-4-6

  codex-cli:
    enabled: true
    mode: cli
    cli_path: codex
    api_key: ${OPENAI_API_KEY}
    default_model: o4-mini
    sandbox: true

  opencode:
    enabled: true
    mode: mcp           # Preferred: richest feature set
    mcp_command: npx -y opencode-mcp
    api_key: ${ANTHROPIC_API_KEY}
    default_model: claude-sonnet-4-5

router:
  strategy: balanced    # cost | quality | balanced
  fallback_timeout_seconds: 60
  cost_limit_per_session: 10.0    # Warn at $10
  cost_limit_per_day: 50.0        # Hard stop at $50

skills:
  directories:
    - ~/.config/agentui/skills/       # User skills
    - ~/Projekte/MyAIGame/portable/   # Portable format skills

focus:
  default_duration_minutes: 15
  celebration: true        # Show celebration on completion
  park_ideas: true         # Enable idea parking
  check_relevance: true    # Check if prompts match focus goal

theme: dark                # dark | light | solarized | custom
```

---

## 10. Implementation Roadmap

### Phase 0: Skeleton (1-2 weeks)

**Goal:** TUI runs, shows a chat, sends prompts to ONE backend.

```
- [ ] Textual app scaffold with basic layout (chat + input)
- [ ] BackendAdapter ABC + ClaudeCodeAdapter (API mode only)
- [ ] Simple prompt → response flow (no streaming yet)
- [ ] SQLite session storage
- [ ] /help command
```

**Done when:** You can type a prompt, see a response from Claude, and it's saved to SQLite.

### Phase 1: Multi-Backend (2-3 weeks)

**Goal:** All three backends work. Manual switching.

```
- [ ] CodexAdapter (CLI mode: spawn codex process)
- [ ] OpenCodeAdapter (MCP mode via Python MCP SDK)
- [ ] Ctrl+1/2/3 backend switching
- [ ] Streaming responses (token by token rendering)
- [ ] Cost tracking per message
- [ ] Session sidebar with backend indicator
```

**Done when:** You can switch between Claude, Codex, and OpenCode mid-conversation.

### Phase 2: Skill Engine (2-3 weeks)

**Goal:** `/skills` work. Universal format loading.

```
- [ ] SKILL.md parser (YAML frontmatter + markdown body)
- [ ] {{tool()}} resolution to backend-specific calls
- [ ] $ARGUMENTS injection
- [ ] Skills panel (F3) with fuzzy search
- [ ] /auto routing (skill → best backend)
- [ ] Fallback chain (60s timeout → next backend)
```

**Done when:** `/chef fix the bug` automatically picks the cheapest capable backend and executes.

### Phase 3: ADHD Features (1-2 weeks)

**Goal:** Focus mode, checkpoints, quick wins as TUI features.

```
- [ ] Focus mode (F5): goal, timer, relevance checking
- [ ] Checkpoint (Ctrl+S): git commit + visual progress
- [ ] Quick Win launcher (Ctrl+Q): scan project, suggest 3 tasks
- [ ] Parked ideas panel
- [ ] Session log with cost tracking
- [ ] Celebration animations
```

**Done when:** Samuel can set a focus goal, work for 15 minutes with gentle nudges, and checkpoint his progress visually.

### Phase 4: Smart Router (1-2 weeks)

**Goal:** Automatic backend selection based on task type, cost, and availability.

```
- [ ] Cost-based routing (cheapest capable backend)
- [ ] Capability matching (sandbox → Codex, sub-agents → Claude/OpenCode)
- [ ] Availability probing (API health checks)
- [ ] Router info panel (F4): show why this backend was chosen
- [ ] Cost budget warnings ($10/session, $50/day)
```

**Done when:** The system picks the right backend automatically and you can see why.

### Phase 5: Polish (ongoing)

```
- [ ] Themes (dark, light, solarized)
- [ ] Mouse support for panel resizing
- [ ] Web preview mode (Textual can serve as web app)
- [ ] Context panel (show modified files, git diff)
- [ ] Multi-session: run research in background while coding
- [ ] Export session to markdown
- [ ] Plugin system for community skills
```

---

## 11. What This Enables

When all phases are done, Samuel's workflow looks like this:

```
$ agentui

  # Start a focus session
  > /focus Fix the authentication timing attack

  # The TUI picks Codex (cheapest) for the code fix
  > /chef fix timing-safe comparison in login.py
  [Routed to Codex CLI | est. $0.15]
  [streaming fix...]

  # Research runs on cheapest available search
  > /research OWASP timing attack best practices
  [Routed to web search | est. $0.00]
  [results...]

  # Heavy orchestration uses Claude Code
  > /test-crew all
  [Routed to Claude Code | est. $0.27]
  [Gemini plans... OpenCode executes... Gemini analyzes...]

  # Checkpoint saves progress visually
  Ctrl+S
  "Fix timing-safe auth" | 3 files | +15 -3 | $0.42 total

  # Focus timer rings
  "15 minutes! 4/5 steps done. Starke Session!"
```

**Total cost for that session:** ~$0.84 (vs ~$15+ if everything went through Opus).

**Zero tool switching.** One terminal, one interface, one set of keybindings.

---

## 12. Open Questions

| Question | Options | Leaning |
|----------|---------|---------|
| Name? | `agentui`, `agenthub`, `omni`, `switchboard` | Ask Samuel |
| Package distribution? | pip, pipx, brew, standalone binary (PyInstaller) | pipx for now, PyInstaller later |
| Backend communication? | CLI subprocess vs API direct vs MCP | All three, adapter decides |
| Session persistence? | SQLite vs JSON files vs both | SQLite (queryable, atomic) |
| Config format? | YAML vs TOML vs JSON | YAML (most readable, Samuel knows it) |
| First backend to build? | Claude Code (most used) vs Codex (simplest API) | Claude Code API mode (most value fast) |
| Voice mode? | First-class or plugin? | Plugin (only works with Claude Code anyway) |
| Community skills? | Local only vs git-based sharing | Local first, git sharing later |

---

## References

- [Bubble Tea](https://github.com/charmbracelet/bubbletea) -- Go TUI framework (OpenCode, Lazygit)
- [Ratatui](https://ratatui.rs/) -- Rust TUI framework
- [Textual](https://textual.textualize.io/) -- Python TUI framework (recommended)
- [OpenCode TUI Architecture](https://deepwiki.com/opencode-ai/opencode/4-terminal-ui-system) -- Bubble Tea MVU pattern
- [Lazygit UX Principles](https://jesseduffield.com/Lazygit-5-Years-On/) -- Consistency, context reduction, interactive guidance
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) -- Official, v1.25.0
- [MCP Go SDK](https://github.com/modelcontextprotocol/go-sdk) -- Official, maintained with Google
- [MCP Rust SDK](https://github.com/modelcontextprotocol/rust-sdk) -- Official
- [Go vs Rust TUI comparison](https://dev.to/dev-tngsh/go-vs-rust-for-tui-development-a-deep-dive-into-bubbletea-and-ratatui-2b7)
- [SPEC.md](./SPEC.md) -- Universal skill format specification
