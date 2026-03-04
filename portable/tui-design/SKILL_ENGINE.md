# TUI Skill Engine & Plugin System Design

> Engine that loads, resolves, and dispatches Universal Skills (SPEC v1.0)
> from any backend (Claude Code, Codex CLI, OpenCode).

---

## 1. Skill Discovery

The engine scans three source trees in priority order. Higher priority wins on name collision.

```
Priority 1 (user global):   ~/.unified-tui/skills/<skill-name>/SKILL.md
Priority 2 (project local): <cwd>/.skills/<skill-name>/SKILL.md
Priority 3 (portable codex): portable/codex/<skill-name>/SKILL.md
Priority 4 (portable oc):   portable/opencode/<skill-name>/SKILL.md
Priority 5 (portable cc):   portable/claude-code/<skill-name>.md
```

Discovery runs at startup and on explicit `reload`. Each discovered skill is parsed
and indexed into the in-memory `SkillRegistry`.

### Directory scan order

```python
SCAN_ROOTS: list[tuple[str, str]] = [
    ("user_global",   "~/.unified-tui/skills/"),
    ("project_local", ".skills/"),
    ("portable_codex","portable/codex/"),
    ("portable_oc",   "portable/opencode/"),
    ("portable_cc",   "portable/claude-code/"),
]
```

For each root the engine walks one level deep, looking for:
- Directory containing `SKILL.md`  → universal skill (has scripts/, references/, assets/)
- Plain `.md` file                  → flat Claude Code style skill

---

## 2. Data Model

```python
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillDependencies:
    tools: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
    external: list[str] = field(default_factory=list)


@dataclass
class AgentRole:
    role: str
    engine: str          # "research" | "code" | "subagent" | "orchestrator"
    description: str


@dataclass
class SkillFrontmatter:
    name: str
    description: str
    argument_hint: str = ""
    category: str = "utility"
    cost_tier: str = "low"
    dependencies: SkillDependencies = field(default_factory=SkillDependencies)
    tags: list[str] = field(default_factory=list)
    agents: list[AgentRole] = field(default_factory=list)


@dataclass
class Skill:
    frontmatter: SkillFrontmatter
    body: str                        # raw markdown body after frontmatter
    source_path: Path                # path to SKILL.md
    source_root: str                 # which scan root found this ("user_global", etc.)
    is_flat: bool = False            # True = plain .md (Claude Code style)

    @property
    def name(self) -> str:
        return self.frontmatter.name

    @property
    def skill_dir(self) -> Path:
        return self.source_path.parent if not self.is_flat else self.source_path.parent
```

---

## 3. Frontmatter Parser

```python
import re
import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_skill_file(path: Path) -> Skill:
    """Parse a SKILL.md or flat .md into a Skill dataclass."""
    raw = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(raw)
    if not m:
        raise ValueError(f"No YAML frontmatter found in {path}")

    fm_raw = yaml.safe_load(m.group(1))
    body = raw[m.end():]

    deps_raw = fm_raw.get("dependencies", {}) or {}
    deps = SkillDependencies(
        tools=deps_raw.get("tools", []),
        scripts=deps_raw.get("scripts", []),
        external=deps_raw.get("external", []),
    )

    agents_raw = fm_raw.get("agents", []) or []
    agents = [AgentRole(**a) for a in agents_raw]

    fm = SkillFrontmatter(
        name=fm_raw["name"],
        description=fm_raw.get("description", ""),
        argument_hint=fm_raw.get("argument-hint", ""),
        category=fm_raw.get("category", "utility"),
        cost_tier=fm_raw.get("cost-tier", "low"),
        dependencies=deps,
        tags=fm_raw.get("tags", []),
        agents=agents,
    )
    is_flat = path.suffix == ".md" and path.name != "SKILL.md"
    return Skill(frontmatter=fm, body=body, source_path=path,
                 source_root="", is_flat=is_flat)
```

---

## 4. Skill Registry

In-memory index built at startup. Supports O(1) name lookup and fuzzy search.

```python
from difflib import get_close_matches


class SkillRegistry:
    """Fast in-memory index of all loaded skills."""

    def __init__(self) -> None:
        self._by_name: dict[str, Skill] = {}
        self._by_category: dict[str, list[Skill]] = {}

    def register(self, skill: Skill) -> None:
        # First registration wins (priority order from scan_roots)
        if skill.name not in self._by_name:
            self._by_name[skill.name] = skill
            cat = skill.frontmatter.category
            self._by_category.setdefault(cat, []).append(skill)

    def get(self, name: str) -> Skill | None:
        return self._by_name.get(name)

    def fuzzy_match(self, query: str, n: int = 5) -> list[Skill]:
        """Return up to n skills whose names are close to query."""
        matches = get_close_matches(query, self._by_name.keys(), n=n, cutoff=0.4)
        return [self._by_name[m] for m in matches]

    def by_category(self, category: str) -> list[Skill]:
        return self._by_category.get(category, [])

    def all(self) -> list[Skill]:
        return list(self._by_name.values())

    def reload(self, roots: list[tuple[str, str]]) -> None:
        self._by_name.clear()
        self._by_category.clear()
        discover_skills(roots, self)
```

---

## 5. Template Resolution

### 5.1 Abstract Tool Syntax

The skill body contains zero or more `{{tool_name(...)}}` placeholders.
These must be resolved to concrete provider calls before execution.

```python
import re
from typing import Callable

# Matches {{tool_name(args)}} — greedy inside parens for multiline support
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\(([^}]*)\)\}\}", re.DOTALL)


@dataclass
class ToolCall:
    name: str           # abstract name, e.g. "delegate_code"
    raw_args: str       # raw argument string from the template


def extract_placeholders(body: str) -> list[ToolCall]:
    return [ToolCall(name=m.group(1), raw_args=m.group(2))
            for m in _PLACEHOLDER_RE.finditer(body)]
```

### 5.2 Argument Substitution

Before template resolution, `$ARGUMENTS` and `$1`-`$9` are replaced with
user-supplied values.

```python
def substitute_arguments(body: str, user_args: str,
                          positional: list[str] | None = None) -> str:
    body = body.replace("$ARGUMENTS", user_args)
    for i, val in enumerate(positional or [], start=1):
        body = body.replace(f"${i}", val)
    return body
```

### 5.3 Backend Tool Mapping

Each backend provides a `ToolResolver` that knows how to map abstract tool names
to concrete calls.

```python
Backend = str  # "claude-code" | "codex" | "opencode"

# Maps abstract tool name -> callable that takes (raw_args, backend) and returns
# the concrete call instruction string (or executes it directly).
ToolHandler = Callable[[str, Backend], str]

TOOL_MAP: dict[str, dict[Backend, ToolHandler]] = {
    "delegate_code": {
        "claude-code":  lambda args, _: f"mcp__opencode__opencode_ask({args})",
        "codex":        lambda args, _: f"codex_run({args})",
        "opencode":     lambda args, _: f"opencode_ask({args})",
    },
    "delegate_code_async": {
        "claude-code":  lambda args, _: f"opencode_session_create + opencode_message_send_async({args})",
        "codex":        lambda args, _: f"codex_run_async({args})",
        "opencode":     lambda args, _: f"opencode_session_create + opencode_message_send_async({args})",
    },
    "delegate_code_run": {
        "claude-code":  lambda args, _: f"mcp__opencode__opencode_run({args})",
        "codex":        lambda args, _: f"codex_run({args})",
        "opencode":     lambda args, _: f"opencode_run({args})",
    },
    "research": {
        "claude-code":  lambda args, _: f"mcp__gemini__ask-gemini({args})",
        "codex":        lambda args, _: f"web_search({args})",
        "opencode":     lambda args, _: f"web_search({args})",
    },
    "spawn_subagent": {
        "claude-code":  lambda args, _: f"Task({args}, run_in_background=True)",
        "codex":        lambda args, _: f"codex_spawn({args})",
        "opencode":     lambda args, _: f"opencode_session_create + opencode_message_send({args})",
    },
    "shell": {
        "claude-code":  lambda args, _: f"Bash({args})",
        "codex":        lambda args, _: f"shell_exec({args})",
        "opencode":     lambda args, _: f"shell_exec({args})",
    },
    "read_file": {
        "claude-code":  lambda args, _: f"Read({args})",
        "codex":        lambda args, _: f"file_read({args})",
        "opencode":     lambda args, _: f"file_read({args})",
    },
    "write_file": {
        "claude-code":  lambda args, _: f"Write({args})",
        "codex":        lambda args, _: f"file_write({args})",
        "opencode":     lambda args, _: f"file_write({args})",
    },
    "search_files": {
        "claude-code":  lambda args, _: f"Grep({args})",
        "codex":        lambda args, _: f"file_search({args})",
        "opencode":     lambda args, _: f"file_search({args})",
    },
    "gather_context": {
        "claude-code":  lambda args, _: f'Bash("~/.claude/hooks/gather-context.sh {args}")',
        "codex":        lambda args, _: f"scripts/gather-context.sh {args}",
        "opencode":     lambda args, _: f"scripts/gather-context.sh {args}",
    },
    "ask_user": {
        "claude-code":  lambda args, _: f"AskUserQuestion({args})",
        "codex":        lambda args, _: f"user_prompt({args})",
        "opencode":     lambda args, _: f"user_prompt({args})",
    },
    "voice_converse": {
        "claude-code":  lambda args, _: f"mcp__voicemode__converse({args})",
        "codex":        lambda args, _: "# voice not supported on codex",
        "opencode":     lambda args, _: "# voice not supported on opencode",
    },
}


def resolve_template(body: str, backend: Backend) -> str:
    """Replace all {{tool(args)}} with backend-specific concrete calls."""
    def replacer(m: re.Match) -> str:
        name = m.group(1)
        args = m.group(2)
        backend_map = TOOL_MAP.get(name)
        if backend_map is None:
            return m.group(0)   # unknown tool — pass through unchanged
        handler = backend_map.get(backend)
        if handler is None:
            return f"# {name} not supported on {backend}"
        return handler(args, backend)

    return _PLACEHOLDER_RE.sub(replacer, body)
```

### 5.4 Target Block Filtering

Skills can include `<!-- target:X -->` raw passthrough blocks. Only the block
matching the active backend is kept; others are stripped.

```python
_TARGET_BLOCK_RE = re.compile(
    r"<!-- target:(\w[\w-]*) -->(.*?)<!-- /target -->",
    re.DOTALL
)


def filter_target_blocks(body: str, backend: Backend) -> str:
    """Keep only the target block for the active backend."""
    def replacer(m: re.Match) -> str:
        target = m.group(1)
        content = m.group(2)
        return content.strip() if target == backend else ""

    return _TARGET_BLOCK_RE.sub(replacer, body)
```

---

## 6. Execution Pipeline

```
user_input
    │
    ▼
parse_skill_invocation()   → (skill_name, user_args, positional)
    │
    ▼
load_skill()               → Skill (from registry)
    │
    ▼
check_dependencies()       → warn if required tools absent on backend
    │
    ▼
substitute_arguments()     → body with $ARGUMENTS / $1-$9 filled
    │
    ▼
filter_target_blocks()     → strip non-matching <!-- target:X --> sections
    │
    ▼
resolve_template()         → body with {{tool(...)}} → concrete calls
    │
    ▼
route_to_provider()        → choose execution strategy based on complexity
    │
    ├─ simple              → execute_direct()   (pass resolved body to LLM)
    ├─ session             → execute_session()  (create session, send body)
    └─ async               → execute_async()    (fire and return session_id)
    │
    ▼
collect_results()          → gather output (streaming / polling)
    │
    ▼
format_output()            → apply output template from skill if present
```

### Python implementation

```python
import shlex
from dataclasses import dataclass


@dataclass
class InvocationRequest:
    skill_name: str
    user_args: str
    positional: list[str]
    backend: Backend


@dataclass
class ExecutionResult:
    skill_name: str
    output: str
    session_id: str | None = None
    is_async: bool = False
    fallback_used: str | None = None


class SkillEngine:
    def __init__(self, registry: SkillRegistry, backend: Backend) -> None:
        self.registry = registry
        self.backend = backend

    def invoke(self, raw_input: str) -> ExecutionResult:
        req = self._parse_invocation(raw_input)
        skill = self._load_skill(req.skill_name)
        self._check_dependencies(skill)
        resolved_body = self._build_prompt(skill, req)
        return self._route_and_execute(skill, resolved_body, req)

    def _parse_invocation(self, raw: str) -> InvocationRequest:
        """Parse '/skill-name arg1 arg2...' or 'skill-name args'."""
        raw = raw.strip()
        if raw.startswith("/"):
            raw = raw[1:]
        parts = shlex.split(raw)
        name = parts[0] if parts else ""
        positional = parts[1:]
        user_args = " ".join(positional)
        return InvocationRequest(
            skill_name=name,
            user_args=user_args,
            positional=positional,
            backend=self.backend,
        )

    def _load_skill(self, name: str) -> Skill:
        skill = self.registry.get(name)
        if skill is None:
            suggestions = self.registry.fuzzy_match(name)
            hint = f" Did you mean: {[s.name for s in suggestions]}?" if suggestions else ""
            raise SkillNotFoundError(f"Unknown skill '{name}'.{hint}")
        return skill

    def _check_dependencies(self, skill: Skill) -> None:
        """Emit warnings for unsupported tools on the active backend."""
        unsupported = []
        for tool in skill.frontmatter.dependencies.tools:
            if tool not in TOOL_MAP or self.backend not in TOOL_MAP.get(tool, {}):
                unsupported.append(tool)
        if unsupported:
            # Non-fatal — warn but continue
            print(f"[warn] Skill '{skill.name}' uses tools not available on "
                  f"{self.backend}: {unsupported}")

    def _build_prompt(self, skill: Skill, req: InvocationRequest) -> str:
        body = substitute_arguments(skill.body, req.user_args, req.positional)
        body = filter_target_blocks(body, req.backend)
        body = resolve_template(body, req.backend)
        return body

    def _route_and_execute(self, skill: Skill, prompt: str,
                           req: InvocationRequest) -> ExecutionResult:
        """Choose execution strategy based on skill complexity."""
        deps = skill.frontmatter.dependencies.tools
        if "delegate_code_async" in deps:
            return self._execute_async(skill, prompt)
        if "spawn_subagent" in deps or skill.frontmatter.category == "multi-agent":
            return self._execute_session(skill, prompt)
        return self._execute_direct(skill, prompt)

    def _execute_direct(self, skill: Skill, prompt: str) -> ExecutionResult:
        # Pass resolved prompt to the active LLM in the current session
        # (implementation is backend-specific; here we return the prompt
        #  for the TUI to forward)
        return ExecutionResult(skill_name=skill.name, output=prompt)

    def _execute_session(self, skill: Skill, prompt: str) -> ExecutionResult:
        # Create a new session and send the resolved prompt
        session_id = f"ses_{skill.name}_{id(prompt)}"
        return ExecutionResult(skill_name=skill.name, output=prompt,
                               session_id=session_id)

    def _execute_async(self, skill: Skill, prompt: str) -> ExecutionResult:
        session_id = f"ses_async_{skill.name}_{id(prompt)}"
        return ExecutionResult(skill_name=skill.name, output=prompt,
                               session_id=session_id, is_async=True)


class SkillNotFoundError(Exception):
    pass
```

---

## 7. Skill Composition

Skills can call other skills by name. The engine detects this pattern in the
resolved body and dispatches recursively with a depth guard.

### 7.1 Composition Syntax (in SKILL.md body)

```markdown
When the task is a coding task: invoke /chef $ARGUMENTS
When the task is a research task: invoke /research $ARGUMENTS
```

### 7.2 Composition Detection & Dispatch

```python
_INVOKE_RE = re.compile(r"\binvoke\s+/(\S+)(?:\s+(.*))?", re.IGNORECASE)
MAX_COMPOSITION_DEPTH = 5


def expand_skill_invocations(body: str, engine: SkillEngine,
                              depth: int = 0) -> str:
    """Replace 'invoke /skill args' with the resolved body of that skill."""
    if depth >= MAX_COMPOSITION_DEPTH:
        return body

    def replacer(m: re.Match) -> str:
        name = m.group(1)
        args = m.group(2) or ""
        try:
            result = engine.invoke(f"{name} {args}")
            return expand_skill_invocations(result.output, engine, depth + 1)
        except SkillNotFoundError:
            return m.group(0)   # leave unknown invocations in place

    return _INVOKE_RE.sub(replacer, body)
```

### 7.3 The /auto Routing Pattern

`/auto` is the canonical composition skill. Its body contains routing logic:

```markdown
Analyze $ARGUMENTS:
- If it is a coding/implementation task: invoke /chef $ARGUMENTS
- If it is a research/information task:  invoke /research $ARGUMENTS
- If it involves multiple sub-tasks:     invoke /batch $ARGUMENTS
- Otherwise: handle directly
```

The engine expands this at runtime — no special-casing in engine code needed.

---

## 8. Plugin API

Third parties can add skills without touching engine code via three mechanisms:

### 8.1 Drop-In Directory (Zero-code)

Place a valid skill directory in `~/.unified-tui/skills/<skill-name>/` or
in the project's `.skills/` directory. The engine picks it up on next reload.

No code changes required. This covers 90% of plugin use cases.

### 8.2 Python Plugin Entry Point (setuptools)

For plugins that need custom tool handlers (new `{{tool_name(...)}}` mappings):

```python
# pyproject.toml
[project.entry-points."unified_tui.tools"]
my_tool = "mypkg.tools:register"

# mypkg/tools.py
from unified_tui.engine import TOOL_MAP, Backend

def register() -> None:
    TOOL_MAP["my_custom_tool"] = {
        "claude-code": lambda args, _: f"mcp__mypkg__my_tool({args})",
        "opencode":    lambda args, _: f"opencode_my_tool({args})",
    }
```

The engine loads all `unified_tui.tools` entry points at startup before
building the registry.

### 8.3 Runtime Plugin API (in-process)

For programmatic plugin registration without setuptools:

```python
from unified_tui.engine import PluginRegistry

class PluginRegistry:
    """Singleton plugin extension point."""

    _tool_handlers:   dict[str, dict[Backend, ToolHandler]] = {}
    _scan_roots:      list[tuple[str, str]] = []
    _result_handlers: list[Callable[[ExecutionResult], None]] = []

    @classmethod
    def register_tool(cls, name: str,
                      handlers: dict[Backend, ToolHandler]) -> None:
        """Add a new abstract tool mapping."""
        TOOL_MAP[name] = handlers

    @classmethod
    def add_scan_root(cls, label: str, path: str) -> None:
        """Add an extra directory to scan for skills."""
        SCAN_ROOTS.append((label, path))

    @classmethod
    def add_result_handler(cls,
                           handler: Callable[[ExecutionResult], None]) -> None:
        """Hook called after every skill execution (for logging, metrics, etc)."""
        cls._result_handlers.append(handler)

    @classmethod
    def run_result_handlers(cls, result: ExecutionResult) -> None:
        for h in cls._result_handlers:
            h(result)
```

### 8.4 Plugin Isolation & Safety

- Plugins run in the same process — no sandbox. Trust model: user installs plugin.
- Unknown frontmatter fields are passed through as YAML comments; engine
  ignores them, so future skill versions don't break older engines.
- Unknown `{{tool_name(...)}}` pass through unmodified with a console warning.
- Maximum composition depth (5) prevents runaway skill recursion.

---

## 9. Skill Discovery Implementation

```python
def discover_skills(roots: list[tuple[str, str]],
                    registry: SkillRegistry) -> None:
    """Walk all scan roots and register discovered skills."""
    for source_root, root_path in roots:
        root = Path(root_path).expanduser().resolve()
        if not root.is_dir():
            continue

        for candidate in sorted(root.iterdir()):
            skill_md = candidate / "SKILL.md"
            if candidate.is_dir() and skill_md.exists():
                # Universal skill (directory layout)
                try:
                    skill = parse_skill_file(skill_md)
                    skill.source_root = source_root
                    registry.register(skill)
                except (ValueError, KeyError) as e:
                    print(f"[warn] Could not parse {skill_md}: {e}")

            elif candidate.is_file() and candidate.suffix == ".md":
                # Flat Claude Code style skill
                try:
                    skill = parse_skill_file(candidate)
                    skill.source_root = source_root
                    skill.is_flat = True
                    registry.register(skill)
                except (ValueError, KeyError) as e:
                    print(f"[warn] Could not parse {candidate}: {e}")
```

---

## 10. Engine Bootstrap

```python
def build_engine(backend: Backend) -> SkillEngine:
    """Full engine startup sequence."""
    # 1. Load plugins from entry points
    _load_entry_point_plugins()

    # 2. Apply runtime plugin scan roots
    roots = SCAN_ROOTS + PluginRegistry._scan_roots

    # 3. Discover and index all skills
    registry = SkillRegistry()
    discover_skills(roots, registry)

    print(f"[skill-engine] {len(registry.all())} skills loaded "
          f"for backend '{backend}'")

    return SkillEngine(registry=registry, backend=backend)


def _load_entry_point_plugins() -> None:
    try:
        import importlib.metadata as meta
        for ep in meta.entry_points(group="unified_tui.tools"):
            ep.load()()
    except Exception as e:
        print(f"[warn] Plugin load error: {e}")
```

---

## 11. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Priority-order scan roots (first wins) | User global overrides project local overrides portable defaults. No surprise merges. |
| In-memory registry | Skills load once at startup. Sub-millisecond lookup. Reload on demand. |
| Regex-based `{{...}}` parser (not AST) | Skills bodies are markdown prose — full AST parser is overkill and fragile. Regex over `{{word(...)}}` is sufficient and predictable. |
| Pass-through on unknown tools | Plugin-added tools and future SPEC tools don't break existing engines. |
| Depth-guarded skill composition | Prevents infinite recursion without requiring static analysis. |
| Entry point plugin API | Industry standard for Python extensibility. Zero coupling to core. |
| `$ARGUMENTS` substituted before template resolution | Argument values may contain content that looks like `{{...}}` — substitute first to avoid double-parsing. |
| Non-fatal dependency warnings | A skill missing one optional tool (e.g. `voice` on Codex) should still run its other steps. |

---

## 12. File Layout Summary

```
portable/
  tui-design/
    SKILL_ENGINE.md      ← this document
  SPEC.md                ← universal skill format spec

~/.unified-tui/
  skills/                ← user-global skill overrides
    <skill-name>/
      SKILL.md

<project>/
  .skills/               ← project-local skills
    <skill-name>/
      SKILL.md

portable/
  claude-code/           ← flat .md skills (Claude Code style)
  codex/                 ← directory skills (Codex style)
  opencode/              ← directory skills (OpenCode style)
```
