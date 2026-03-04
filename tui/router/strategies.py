"""Routing strategies for the MyAIGame smart router.

Each strategy implements RoutingStrategy.route() and returns a ranked
list of providers. The SmartRouter combines them with weighted scoring.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Domain types  (mirrors SMART_ROUTER.md §1)
# ---------------------------------------------------------------------------

class Provider(str, Enum):
    CLAUDE_CODE = "claude-code"   # Opus 4.6 — orchestrator, best reasoning
    OPENCODE    = "opencode"      # Sonnet — code generation, sub-agents
    CODEX       = "codex"         # Codex CLI — sandboxed execution
    GEMINI      = "gemini"        # Flash — cheap research, fact-checking
    DIRECT      = "direct"        # No LLM, pure shell/script execution


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
# Routing constants
# ---------------------------------------------------------------------------

# Per-provider approximate cost multiplier (relative to cheapest)
PROVIDER_COST_RANK: dict[Provider, int] = {
    Provider.DIRECT:      0,   # free
    Provider.GEMINI:      1,   # ~$0.10/1M tokens
    Provider.OPENCODE:    3,   # ~$3/1M (Sonnet)
    Provider.CODEX:       3,   # ~$3/1M (similar tier)
    Provider.CLAUDE_CODE: 15,  # ~$15/1M (Opus)
}

# Which providers are acceptable per cost tier (ceiling)
COST_TIER_CEILING: dict[CostTier, set[Provider]] = {
    CostTier.FREE:     {Provider.DIRECT},
    CostTier.MINIMAL:  {Provider.DIRECT, Provider.GEMINI},
    CostTier.LOW:      {Provider.DIRECT, Provider.GEMINI, Provider.OPENCODE, Provider.CODEX},
    CostTier.MEDIUM:   {Provider.DIRECT, Provider.GEMINI, Provider.OPENCODE, Provider.CODEX},
    CostTier.HIGH:     {Provider.DIRECT, Provider.GEMINI, Provider.OPENCODE, Provider.CODEX, Provider.CLAUDE_CODE},
    CostTier.VARIABLE: {Provider.DIRECT, Provider.GEMINI, Provider.OPENCODE, Provider.CODEX, Provider.CLAUDE_CODE},
}

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
        "sandbox",  # Codex has a sandbox — critical for untrusted code execution
    },
    Provider.CLAUDE_CODE: {
        "delegate_code", "delegate_code_async", "delegate_code_session",
        "delegate_code_run", "spawn_subagent", "shell", "file_read",
        "file_write", "file_search", "glob_files", "git", "research",
        "voice",
        "orchestrate", "reason_complex",  # Claude Code = orchestrator, best reasoning
    },
}


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class RoutingStrategy(ABC):
    """Base interface for all routing strategies."""

    @abstractmethod
    def route(
        self,
        skill_meta: SkillMetadata,
        providers: dict[Provider, ProviderHealth],
    ) -> list[Provider]:
        """Return providers ranked best-first for this skill."""
        ...


# ---------------------------------------------------------------------------
# CostBasedStrategy — picks cheapest provider for the skill's cost tier
# ---------------------------------------------------------------------------

class CostBasedStrategy(RoutingStrategy):
    """Pick the cheapest provider that can handle the skill's cost tier.

    Respects both the skill's cost_tier and the user's max_cost_tier ceiling.
    """

    def __init__(self, prefs: UserPreferences | None = None) -> None:
        self._prefs = prefs or UserPreferences()

    def route(
        self,
        skill_meta: SkillMetadata,
        providers: dict[Provider, ProviderHealth],
    ) -> list[Provider]:
        acceptable = COST_TIER_CEILING.get(skill_meta.cost_tier, set())
        user_ceiling = COST_TIER_CEILING.get(self._prefs.max_cost_tier, set())
        candidates = acceptable & user_ceiling

        healthy = [
            p for p in candidates
            if providers.get(p, ProviderHealth(p)).available
            and not providers.get(p, ProviderHealth(p)).rate_limited
        ]

        # Sort cheapest first
        return sorted(healthy, key=lambda p: PROVIDER_COST_RANK[p])


# ---------------------------------------------------------------------------
# CapabilityBasedStrategy — matches skill requirements to provider capabilities
# ---------------------------------------------------------------------------

class CapabilityBasedStrategy(RoutingStrategy):
    """Pick providers that have ALL required tools for the skill.

    Prefers providers with the smallest capability superset (most specialised)
    to avoid over-powered backends for simple tasks.
    """

    def route(
        self,
        skill_meta: SkillMetadata,
        providers: dict[Provider, ProviderHealth],
    ) -> list[Provider]:
        required = set(skill_meta.dependencies)

        capable = [
            p for p, caps in PROVIDER_CAPABILITIES.items()
            if required.issubset(caps)
            and providers.get(p, ProviderHealth(p)).available
            and not providers.get(p, ProviderHealth(p)).rate_limited
        ]

        def capability_surplus(p: Provider) -> int:
            return len(PROVIDER_CAPABILITIES[p]) - len(required)

        return sorted(capable, key=capability_surplus)


# ---------------------------------------------------------------------------
# UserOverrideStrategy — respects pinned skill→provider mappings from config
# ---------------------------------------------------------------------------

class UserOverrideStrategy(RoutingStrategy):
    """Return the user-pinned provider for a skill, if configured.

    When a skill is pinned, this strategy returns only that provider.
    Returns an empty list when there is no pin (let other strategies decide).
    """

    def __init__(self, prefs: UserPreferences) -> None:
        self._prefs = prefs

    def route(
        self,
        skill_meta: SkillMetadata,
        providers: dict[Provider, ProviderHealth],
    ) -> list[Provider]:
        pinned = self._prefs.pinned_skills.get(skill_meta.name)
        if pinned is None:
            return []

        h = providers.get(pinned, ProviderHealth(pinned))
        if h.available and not h.rate_limited:
            return [pinned]

        # Pinned provider is down — return it anyway so the caller can
        # apply fallback logic rather than silently ignoring the pin.
        return [pinned]
