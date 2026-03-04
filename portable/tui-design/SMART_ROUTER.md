# Smart Routing Engine — TUI Design

> Automatically picks the best backend per skill invocation based on cost, capability,
> availability, and user preferences.

---

## 1. Routing Strategies

All four routers share a common interface. The `HybridRouter` composes them.

```python
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class Provider(str, Enum):
    CLAUDE_CODE  = "claude-code"   # Opus 4.6 — orchestrator, best reasoning
    OPENCODE     = "opencode"      # Sonnet — code generation, sub-agents
    CODEX        = "codex"         # Codex CLI — sandboxed execution
    GEMINI       = "gemini"        # Flash — cheap research, fact-checking
    DIRECT       = "direct"        # No LLM, pure shell/script execution


class CostTier(str, Enum):
    FREE     = "free"      # $0
    MINIMAL  = "minimal"   # < $0.05
    LOW      = "low"       # $0.05–$0.30
    MEDIUM   = "medium"    # $0.30–$1.00
    HIGH     = "high"      # $1.00–$5.00
    VARIABLE = "variable"  # scales with input


class Category(str, Enum):
    DELEGATION  = "delegation"
    RESEARCH    = "research"
    TESTING     = "testing"
    MULTI_AGENT = "multi-agent"
    WORKFLOW    = "workflow"
    UTILITY     = "utility"
    META        = "meta"
    VOICE       = "voice"


@dataclass
class SkillMetadata:
    name: str
    category: Category
    cost_tier: CostTier
    dependencies: list[str]          # abstract tool names from SPEC.md §2.3
    tags: list[str] = field(default_factory=list)
    complexity: str = "simple"       # simple | medium | complex | routing | iterative


@dataclass
class ProviderHealth:
    provider: Provider
    available: bool = True
    latency_ms: float = 0.0
    rate_limited: bool = False
    last_checked: float = field(default_factory=time.time)


@dataclass
class UserPreferences:
    max_cost_tier: CostTier = CostTier.HIGH
    pinned_skills: dict[str, Provider] = field(default_factory=dict)
    prefer_offline: bool = False
    budget_per_session_usd: float = 5.0


@dataclass
class RoutingDecision:
    primary: Provider
    fallback_chain: list[Provider]
    rationale: str
    estimated_cost_tier: CostTier


# ---------------------------------------------------------------------------
# 1.1  CostBasedRouter
# ---------------------------------------------------------------------------

# Per-provider approximate cost multiplier (relative to cheapest)
PROVIDER_COST_RANK: dict[Provider, int] = {
    Provider.DIRECT:      0,   # free
    Provider.GEMINI:      1,   # ~$0.10/1M tokens
    Provider.OPENCODE:    3,   # ~$3/1M (Sonnet)
    Provider.CODEX:       3,   # ~$3/1M (similar tier)
    Provider.CLAUDE_CODE: 15,  # ~$15/1M (Opus)
}

# Which providers are acceptable per cost tier
COST_TIER_CEILING: dict[CostTier, set[Provider]] = {
    CostTier.FREE:     {Provider.DIRECT},
    CostTier.MINIMAL:  {Provider.DIRECT, Provider.GEMINI},
    CostTier.LOW:      {Provider.DIRECT, Provider.GEMINI, Provider.OPENCODE, Provider.CODEX},
    CostTier.MEDIUM:   {Provider.DIRECT, Provider.GEMINI, Provider.OPENCODE, Provider.CODEX},
    CostTier.HIGH:     {Provider.DIRECT, Provider.GEMINI, Provider.OPENCODE, Provider.CODEX, Provider.CLAUDE_CODE},
    CostTier.VARIABLE: {Provider.DIRECT, Provider.GEMINI, Provider.OPENCODE, Provider.CODEX, Provider.CLAUDE_CODE},
}


class CostBasedRouter:
    """Pick the cheapest provider that can handle the skill's cost tier."""

    def route(
        self,
        skill: SkillMetadata,
        health: dict[Provider, ProviderHealth],
        prefs: UserPreferences,
    ) -> list[Provider]:
        acceptable = COST_TIER_CEILING.get(skill.cost_tier, set())
        # Also respect user's max cost ceiling
        user_ceiling = COST_TIER_CEILING.get(prefs.max_cost_tier, set())
        candidates = acceptable & user_ceiling

        # Filter to healthy providers
        healthy = [p for p in candidates if health.get(p, ProviderHealth(p)).available
                   and not health.get(p, ProviderHealth(p)).rate_limited]

        # Sort by cost (cheapest first)
        return sorted(healthy, key=lambda p: PROVIDER_COST_RANK[p])


# ---------------------------------------------------------------------------
# 1.2  CapabilityBasedRouter
# ---------------------------------------------------------------------------

# Which abstract tools each provider supports
PROVIDER_CAPABILITIES: dict[Provider, set[str]] = {
    Provider.DIRECT: {
        "shell", "file_read", "file_write", "file_search", "glob_files", "git",
    },
    Provider.GEMINI: {
        "research", "file_read",
    },
    Provider.OPENCODE: {
        "delegate_code", "delegate_code_async", "delegate_code_session",
        "delegate_code_run", "spawn_subagent", "shell", "file_read",
        "file_write", "file_search", "glob_files", "git", "research",
    },
    Provider.CODEX: {
        "delegate_code", "delegate_code_run", "shell", "file_read",
        "file_write", "file_search", "glob_files", "git", "research",
        # Codex has a sandbox — critical for untrusted code execution
        "sandbox",
    },
    Provider.CLAUDE_CODE: {
        "delegate_code", "delegate_code_async", "delegate_code_session",
        "delegate_code_run", "spawn_subagent", "shell", "file_read",
        "file_write", "file_search", "glob_files", "git", "research",
        "voice",
        # Claude Code = orchestrator, best reasoning
        "orchestrate", "reason_complex",
    },
}


class CapabilityBasedRouter:
    """Pick providers that have ALL required tools for the skill."""

    def route(
        self,
        skill: SkillMetadata,
        health: dict[Provider, ProviderHealth],
        prefs: UserPreferences,
    ) -> list[Provider]:
        required = set(skill.dependencies)

        capable = [
            p for p, caps in PROVIDER_CAPABILITIES.items()
            if required.issubset(caps)
            and health.get(p, ProviderHealth(p)).available
            and not health.get(p, ProviderHealth(p)).rate_limited
        ]

        # Prefer providers with the smallest capability superset (most specialised)
        def capability_surplus(p: Provider) -> int:
            return len(PROVIDER_CAPABILITIES[p]) - len(required)

        return sorted(capable, key=capability_surplus)


# ---------------------------------------------------------------------------
# 1.3  AvailabilityRouter
# ---------------------------------------------------------------------------

# Default fallback chain when provider is unhealthy
FALLBACK_CHAINS: dict[Provider, list[Provider]] = {
    Provider.CLAUDE_CODE: [Provider.OPENCODE, Provider.CODEX, Provider.DIRECT],
    Provider.OPENCODE:    [Provider.CODEX, Provider.CLAUDE_CODE, Provider.DIRECT],
    Provider.CODEX:       [Provider.OPENCODE, Provider.CLAUDE_CODE, Provider.DIRECT],
    Provider.GEMINI:      [Provider.OPENCODE, Provider.CLAUDE_CODE],  # research fallback
    Provider.DIRECT:      [],  # no fallback — shell is the last resort
}

TIMEOUT_SECONDS = 60  # from SPEC.md §9.3


class AvailabilityRouter:
    """Return a healthy provider and a fallback chain. Respects 60s timeout pattern."""

    def route(
        self,
        preferred: Provider,
        health: dict[Provider, ProviderHealth],
    ) -> RoutingDecision:
        h = health.get(preferred, ProviderHealth(preferred))

        if h.available and not h.rate_limited:
            primary = preferred
            rationale = f"{preferred.value} is healthy"
        else:
            reason = "rate-limited" if h.rate_limited else "unavailable"
            chain = FALLBACK_CHAINS.get(preferred, [])
            healthy_fallbacks = [
                p for p in chain
                if health.get(p, ProviderHealth(p)).available
                and not health.get(p, ProviderHealth(p)).rate_limited
            ]
            if not healthy_fallbacks:
                primary = Provider.DIRECT
                rationale = f"{preferred.value} {reason}; all fallbacks down — using direct shell"
            else:
                primary = healthy_fallbacks[0]
                rationale = (
                    f"{preferred.value} {reason}; "
                    f"falling back to {primary.value} "
                    f"(timeout: {TIMEOUT_SECONDS}s)"
                )
            chain = healthy_fallbacks

        return RoutingDecision(
            primary=primary,
            fallback_chain=FALLBACK_CHAINS.get(primary, []),
            rationale=rationale,
            estimated_cost_tier=CostTier.VARIABLE,
        )


# ---------------------------------------------------------------------------
# 1.4  HybridRouter  (combines all three with weighted scoring)
# ---------------------------------------------------------------------------

# Weight coefficients — tune these to taste
W_COST         = 0.40   # 40% — keep bills low by default
W_CAPABILITY   = 0.40   # 40% — must have the tools
W_AVAILABILITY = 0.20   # 20% — prefer healthy, but don't sacrifice quality

PROVIDER_ORDER = [
    Provider.DIRECT,
    Provider.GEMINI,
    Provider.OPENCODE,
    Provider.CODEX,
    Provider.CLAUDE_CODE,
]


class HybridRouter:
    """
    Weighted combination of cost, capability, and availability scores.

    Final score = W_COST * cost_score
                + W_CAPABILITY * capability_score
                + W_AVAILABILITY * availability_score

    Higher score = better choice.
    """

    def __init__(self) -> None:
        self._cost_router = CostBasedRouter()
        self._cap_router  = CapabilityBasedRouter()

    def route(
        self,
        skill: SkillMetadata,
        health: dict[Provider, ProviderHealth],
        prefs: UserPreferences,
    ) -> RoutingDecision:
        # --- User pin overrides everything ---
        if skill.name in prefs.pinned_skills:
            pinned = prefs.pinned_skills[skill.name]
            avail_router = AvailabilityRouter()
            decision = avail_router.route(pinned, health)
            decision.rationale = f"User pin: {pinned.value}. " + decision.rationale
            return decision

        scores: dict[Provider, float] = {p: 0.0 for p in Provider}

        # Cost score: cheaper → higher score
        cost_ranked = self._cost_router.route(skill, health, prefs)
        n_cost = len(cost_ranked)
        for rank, provider in enumerate(cost_ranked):
            scores[provider] += W_COST * (n_cost - rank) / max(n_cost, 1)

        # Capability score: capable → higher score
        cap_ranked = self._cap_router.route(skill, health, prefs)
        n_cap = len(cap_ranked)
        for rank, provider in enumerate(cap_ranked):
            scores[provider] += W_CAPABILITY * (n_cap - rank) / max(n_cap, 1)

        # Availability score: healthy + low latency → higher score
        for provider, h in health.items():
            if h.available and not h.rate_limited:
                latency_bonus = max(0.0, 1.0 - h.latency_ms / 5000.0)
                scores[provider] += W_AVAILABILITY * latency_bonus

        # Sort by descending score; must appear in both cost and cap lists
        eligible = set(cost_ranked) & set(cap_ranked)
        ranked = sorted(eligible, key=lambda p: scores[p], reverse=True)

        if not ranked:
            # Last resort
            primary = Provider.DIRECT
            fallback = []
            rationale = "No eligible provider found — falling back to direct shell execution"
        else:
            primary = ranked[0]
            fallback = [p for p in ranked[1:]] + FALLBACK_CHAINS.get(primary, [])
            # Deduplicate while preserving order
            seen: set[Provider] = {primary}
            deduped_fallback: list[Provider] = []
            for p in fallback:
                if p not in seen:
                    seen.add(p)
                    deduped_fallback.append(p)
            fallback = deduped_fallback

            rationale = (
                f"Hybrid score: {primary.value} ({scores[primary]:.2f}). "
                f"Cost rank: {cost_ranked.index(primary) + 1}/{n_cost}. "
                f"Capability rank: {cap_ranked.index(primary) + 1}/{n_cap}."
            )

        return RoutingDecision(
            primary=primary,
            fallback_chain=fallback,
            rationale=rationale,
            estimated_cost_tier=skill.cost_tier,
        )
```

---

## 2. Decision Tree

```
SKILL INVOCATION
      │
      ▼
┌─────────────────────────────┐
│  User pin for this skill?   │──YES──► Use pinned provider
│  (prefs.pinned_skills)      │         └─► AvailabilityRouter for fallback
└─────────────┬───────────────┘
              │ NO
              ▼
┌─────────────────────────────┐
│  skill.cost_tier == FREE    │──YES──► Provider.DIRECT
│  or MINIMAL?                │         (no LLM needed)
└─────────────┬───────────────┘
              │ NO
              ▼
┌─────────────────────────────────────────────────────┐
│  CostBasedRouter: which providers fit cost ceiling? │
│  CapabilityRouter: which providers have all tools?  │
│  Intersection = eligible set                        │
└─────────────────────┬───────────────────────────────┘
                      │
              eligible set empty?
              ├── YES ──► DIRECT (last resort)
              │
              └── NO
                      │
                      ▼
        ┌─────────────────────────┐
        │  HybridRouter scoring   │
        │  40% cost + 40% cap     │
        │  + 20% availability     │
        └────────────┬────────────┘
                     │
                     ▼
              primary = ranked[0]
                     │
              ┌──────┴──────┐
              │             │
         HEALTHY?        UNHEALTHY / RATE-LIMITED
              │             │
              ▼             ▼
        EXECUTE      AvailabilityRouter
                     └─► try fallback_chain[0]
                               │
                         stalls > 60s?
                         ├── YES ──► try fallback_chain[1]
                         │           (tell user which fallback)
                         └── NO  ──► continue with fallback_chain[0]
                               │
                         all fallbacks exhausted?
                               └── YES ──► DIRECT + user caveat
```

### Input signals summary

| Signal | Source | Used by |
|--------|--------|---------|
| `skill.category` | SKILL.md frontmatter | CapabilityRouter |
| `skill.cost_tier` | SKILL.md frontmatter | CostBasedRouter |
| `skill.dependencies` | SKILL.md frontmatter | CapabilityRouter |
| `prefs.max_cost_tier` | User config / TUI setting | CostBasedRouter |
| `prefs.pinned_skills` | User config | HybridRouter (early exit) |
| `health[provider].available` | Health-check ping | AvailabilityRouter |
| `health[provider].rate_limited` | API response header | AvailabilityRouter |
| `health[provider].latency_ms` | Measured round-trip | HybridRouter scoring |

---

## 3. Routing Table — All 30 Skills

Primary = ideal backend under normal conditions.
Fallback = next in chain if primary fails or is rate-limited.

| # | Skill | Category | Cost | Primary | Fallback(s) | Rationale |
|---|-------|----------|------|---------|-------------|-----------|
| 1 | `auto` | delegation | variable | OPENCODE | CODEX → CLAUDE_CODE | routing skill itself; Sonnet handles meta-routing cheaply |
| 2 | `batch` | delegation | low | OPENCODE | CODEX → DIRECT | bulk delegation; Sonnet cost-effective |
| 3 | `bigwin` | workflow | free | DIRECT | — | file read/write only, no LLM |
| 4 | `check-state` | utility | free | DIRECT | — | shell + file_read, no LLM |
| 5 | `checkpoint` | workflow | free | DIRECT | — | git shell commands only |
| 6 | `chef` | delegation | low | OPENCODE | CODEX → CLAUDE_CODE | context-enhanced delegation, needs delegate_code_run |
| 7 | `chef-async` | delegation | low | OPENCODE | CODEX | async session; OpenCode native async |
| 8 | `chef-lite` | delegation | minimal | OPENCODE | CODEX → CLAUDE_CODE | simple one-shot; Sonnet cheapest capable |
| 9 | `chef-subagent` | delegation | low | OPENCODE | CLAUDE_CODE | needs spawn_subagent; OpenCode best sub-agent support |
| 10 | `ChromeExtension` | utility | free | DIRECT | — | shell only |
| 11 | `crew` | multi-agent | high | CLAUDE_CODE | OPENCODE | external script + best reasoning needed |
| 12 | `debug-loop` | utility | variable | OPENCODE | CODEX → DIRECT | iterative; Sonnet cost-effective for loops |
| 13 | `delegate` | delegation | low | OPENCODE | CODEX → CLAUDE_CODE | full delegation with complexity check |
| 14 | `explore-first` | utility | low | OPENCODE | CLAUDE_CODE | spawn_subagent required |
| 15 | `focus` | workflow | free | DIRECT | — | file_write only |
| 16 | `learn` | meta | free | DIRECT | — | git + file_read/write, no LLM |
| 17 | `quickwin` | workflow | free | DIRECT | — | git + search_files, no LLM |
| 18 | `recap` | workflow | free | DIRECT | — | file_write only |
| 19 | `research` | research | low | GEMINI | OPENCODE → CLAUDE_CODE | cheapest research engine (~$0.10/1M) |
| 20 | `research-subagent` | research | low | OPENCODE | CLAUDE_CODE | spawn_subagent + research; Haiku via OpenCode |
| 21 | `research-swarm` | research | medium | OPENCODE | CLAUDE_CODE | 3x parallel research; OpenCode session management |
| 22 | `review` | utility | free | DIRECT | — | shell + file_read + search |
| 23 | `selfimprove` | meta | free | DIRECT | — | file_read + edit_file only |
| 24 | `setup-git` | utility | free | DIRECT | — | git shell only |
| 25 | `snapshot` | utility | free | DIRECT | — | shell script only |
| 26 | `swarm` | multi-agent | variable | OPENCODE | CLAUDE_CODE | spawn_subagent x3+; OpenCode best sub-agent support |
| 27 | `test` | testing | medium | OPENCODE | CODEX → CLAUDE_CODE | delegate_code + research combo |
| 28 | `test-crew` | testing | medium | OPENCODE | CODEX → CLAUDE_CODE | same as test with crew pattern |
| 29 | `validate-config` | utility | free | DIRECT | GEMINI | file_read + shell; research only if needed |
| 30 | `voice-smart` | voice | variable | CLAUDE_CODE | — | only Claude Code supports voice tool |

### Cost summary by primary provider

| Provider | Skills routed here | Pct |
|----------|-------------------|-----|
| DIRECT | bigwin, check-state, checkpoint, ChromeExtension, focus, learn, quickwin, recap, review, selfimprove, setup-git, snapshot | 40% |
| OPENCODE | auto, batch, chef, chef-async, chef-lite, chef-subagent, debug-loop, delegate, explore-first, research-subagent, research-swarm, swarm, test, test-crew | 47% |
| GEMINI | research | 3% |
| CLAUDE_CODE | crew, voice-smart | 7% |
| CODEX | — (fallback only) | 0% primary |

---

## 4. User Override — Pinning Skills to Backends

### 4.1 Config file

```yaml
# ~/.myaigame/router.yaml  (or per-project .myaigame/router.yaml)

routing:
  max_cost_tier: medium        # never exceed medium cost
  prefer_offline: false        # if true, prefer DIRECT wherever possible
  budget_per_session_usd: 2.0

  # Pin specific skills to specific backends
  # Overrides ALL routing logic — hard pin
  pins:
    research: gemini           # always use Gemini for /research
    crew: claude-code          # always use Claude Code for /crew
    chef: opencode             # always use OpenCode for /chef
    # voice-smart: claude-code  # already the only option, but explicit is fine
```

### 4.2 TUI override (runtime)

Users can change pins interactively during a session:

```
/router pin research gemini     # hard-pin for this session
/router pin chef opencode       # override cost routing
/router unpin research          # remove pin, let HybridRouter decide
/router status                  # show current routing table + health
/router cost-limit medium       # set max cost tier ceiling
```

### 4.3 Python API for TUI integration

```python
@dataclass
class RouterConfig:
    config_path: str = "~/.myaigame/router.yaml"
    prefs: UserPreferences = field(default_factory=UserPreferences)

    def pin(self, skill_name: str, provider: Provider) -> None:
        self.prefs.pinned_skills[skill_name] = provider
        self._persist()

    def unpin(self, skill_name: str) -> None:
        self.prefs.pinned_skills.pop(skill_name, None)
        self._persist()

    def set_max_cost(self, tier: CostTier) -> None:
        self.prefs.max_cost_tier = tier
        self._persist()

    def _persist(self) -> None:
        import yaml, os
        path = os.path.expanduser(self.config_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            yaml.dump({"routing": {
                "max_cost_tier": self.prefs.max_cost_tier.value,
                "pins": {k: v.value for k, v in self.prefs.pinned_skills.items()},
                "budget_per_session_usd": self.prefs.budget_per_session_usd,
            }}, f)
```

---

## 5. Fallback Chains

### 5.1 The 60-second timeout pattern (from SPEC.md §9.3)

```python
import asyncio
from typing import Callable, Any

async def execute_with_fallback(
    skill: SkillMetadata,
    decision: RoutingDecision,
    execute_fn: Callable[[Provider, SkillMetadata], Any],
    notify_fn: Callable[[str], None],
    timeout: float = 60.0,
) -> Any:
    """
    Try primary provider. If it stalls > timeout seconds,
    walk the fallback chain. Notify user at each switch.
    """
    chain = [decision.primary] + decision.fallback_chain

    for i, provider in enumerate(chain):
        if i > 0:
            notify_fn(
                f"{chain[i-1].value} not responding after {timeout}s "
                f"-- switching to {provider.value}"
            )

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(execute_fn, provider, skill),
                timeout=timeout,
            )
            if i > 0:
                notify_fn(f"Completed via {provider.value} (fallback #{i})")
            return result

        except asyncio.TimeoutError:
            continue  # try next in chain

        except Exception as e:
            notify_fn(f"{provider.value} error: {e} -- trying next fallback")
            continue

    # All fallbacks exhausted
    notify_fn(
        "All providers failed or timed out. "
        "Attempting direct shell execution as last resort."
    )
    return execute_fn(Provider.DIRECT, skill)
```

### 5.2 Fallback chains by category

| Category | Primary | Fallback 1 | Fallback 2 | Last Resort |
|----------|---------|------------|------------|-------------|
| research | GEMINI | OPENCODE (WebSearch) | CLAUDE_CODE (own knowledge) | Direct (own knowledge + caveat) |
| delegation | OPENCODE | CODEX | CLAUDE_CODE | DIRECT (Bash) |
| multi-agent | CLAUDE_CODE | OPENCODE | — | Error: sub-agents required |
| testing | OPENCODE | CODEX | CLAUDE_CODE | DIRECT (run tests manually) |
| workflow | DIRECT | — | — | — (always works) |
| utility | DIRECT | — | — | — (always works) |
| meta | DIRECT | — | — | — (always works) |
| voice | CLAUDE_CODE | — | — | Error: voice not supported elsewhere |

### 5.3 Health check loop

```python
import threading

class HealthMonitor:
    """Background thread that pings providers every 30s."""

    CHECK_INTERVAL = 30.0  # seconds
    PING_TIMEOUT   = 5.0   # seconds per provider

    def __init__(self) -> None:
        self._health: dict[Provider, ProviderHealth] = {
            p: ProviderHealth(p) for p in Provider
        }
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def get(self) -> dict[Provider, ProviderHealth]:
        with self._lock:
            return dict(self._health)

    def _ping(self, provider: Provider) -> ProviderHealth:
        import time
        t0 = time.monotonic()
        try:
            # Each provider has a lightweight probe (list models, ping endpoint, etc.)
            _PROBES[provider]()
            latency = (time.monotonic() - t0) * 1000
            return ProviderHealth(provider, available=True, latency_ms=latency)
        except RateLimitError:
            return ProviderHealth(provider, available=True, rate_limited=True)
        except Exception:
            return ProviderHealth(provider, available=False)

    def _loop(self) -> None:
        import time
        while True:
            for provider in Provider:
                if provider == Provider.DIRECT:
                    continue  # always available
                h = self._ping(provider)
                with self._lock:
                    self._health[provider] = h
            time.sleep(self.CHECK_INTERVAL)


class RateLimitError(Exception):
    pass

# Provider probe stubs — implement with actual SDK calls
_PROBES: dict[Provider, Callable[[], None]] = {
    Provider.GEMINI:      lambda: None,  # e.g. mcp__gemini__ping()
    Provider.OPENCODE:    lambda: None,  # e.g. opencode_status()
    Provider.CODEX:       lambda: None,  # e.g. codex --version
    Provider.CLAUDE_CODE: lambda: None,  # always available (we ARE Claude Code)
    Provider.DIRECT:      lambda: None,
}
```

---

## 6. Putting It All Together — Router Entry Point

```python
# tui/router.py

class SmartRouter:
    """Top-level router used by the TUI skill dispatcher."""

    def __init__(self, config: RouterConfig, monitor: HealthMonitor) -> None:
        self._config  = config
        self._monitor = monitor
        self._hybrid  = HybridRouter()

    def decide(self, skill: SkillMetadata) -> RoutingDecision:
        health = self._monitor.get()
        prefs  = self._config.prefs
        return self._hybrid.route(skill, health, prefs)

    async def dispatch(
        self,
        skill: SkillMetadata,
        execute_fn: Callable[[Provider, SkillMetadata], Any],
        notify_fn: Callable[[str], None],
    ) -> Any:
        decision = self.decide(skill)
        notify_fn(f"Routing /{skill.name} → {decision.primary.value}  ({decision.rationale})")
        return await execute_with_fallback(skill, decision, execute_fn, notify_fn)
```

### Example invocation flow

```
User types: /research "best Python async patterns 2026"
     │
     ▼
SmartRouter.dispatch(skill=research_metadata, ...)
     │
     ├─ HybridRouter: cost=GEMINI(1), cap=GEMINI(1), health=OK
     │   → primary=GEMINI, fallback=[OPENCODE, CLAUDE_CODE]
     │
     ├─ TUI notifies: "Routing /research → gemini (cost rank 1/2, cap rank 1/2)"
     │
     ├─ execute_with_fallback: tries GEMINI, timeout=60s
     │   ├─ GEMINI responds in 3s → return result
     │   └─ (if stalled 60s → switch to OPENCODE, notify user)
     │
     └─ Result displayed in TUI
```

---

## Version

| Version | Date | Author |
|---------|------|--------|
| 1.0 | 2026-02-26 | myaigame-portable agent team |
