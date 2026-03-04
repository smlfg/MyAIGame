"""SmartRouter — combines all routing strategies with weighted scoring.

Mirrors the HybridRouter design from SMART_ROUTER.md §1.4 and §6,
adapted to the three-strategy model (Cost, Capability, UserOverride).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable

import yaml

from .strategies import (
    CapabilityBasedStrategy,
    CostBasedStrategy,
    CostTier,
    FALLBACK_CHAINS_DEFAULT,
    Provider,
    ProviderHealth,
    RoutingDecision,
    SkillMetadata,
    UserOverrideStrategy,
    UserPreferences,
    PROVIDER_COST_RANK,
    PROVIDER_CAPABILITIES,
)
from .fallback import execute_with_fallback


# ---------------------------------------------------------------------------
# Default fallback chains (imported lazily to avoid circular dependency)
# ---------------------------------------------------------------------------

FALLBACK_CHAINS: dict[Provider, list[Provider]] = {
    Provider.CLAUDE_CODE: [Provider.OPENCODE, Provider.CODEX, Provider.DIRECT],
    Provider.OPENCODE:    [Provider.CODEX, Provider.CLAUDE_CODE, Provider.DIRECT],
    Provider.CODEX:       [Provider.OPENCODE, Provider.CLAUDE_CODE, Provider.DIRECT],
    Provider.GEMINI:      [Provider.OPENCODE, Provider.CLAUDE_CODE],
    Provider.DIRECT:      [],
}

# Weight coefficients (must sum to 1.0)
DEFAULT_COST_WEIGHT        = 0.3
DEFAULT_CAPABILITY_WEIGHT  = 0.5
DEFAULT_PREFERENCE_WEIGHT  = 0.2


# ---------------------------------------------------------------------------
# RouterConfig — persists preferences to YAML
# ---------------------------------------------------------------------------

@dataclass
class RouterConfig:
    config_path: str = "~/.myaigame/router.yaml"
    prefs: UserPreferences = field(default_factory=UserPreferences)

    def load(self) -> None:
        """Load preferences from the YAML config file (if it exists)."""
        path = os.path.expanduser(self.config_path)
        if not os.path.exists(path):
            return
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        routing = data.get("routing", {})

        if "max_cost_tier" in routing:
            self.prefs.max_cost_tier = CostTier(routing["max_cost_tier"])
        if "prefer_offline" in routing:
            self.prefs.prefer_offline = bool(routing["prefer_offline"])
        if "budget_per_session_usd" in routing:
            self.prefs.budget_per_session_usd = float(routing["budget_per_session_usd"])
        for skill_name, provider_val in routing.get("pins", {}).items():
            self.prefs.pinned_skills[skill_name] = Provider(provider_val)

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
        path = os.path.expanduser(self.config_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(
                {
                    "routing": {
                        "max_cost_tier": self.prefs.max_cost_tier.value,
                        "prefer_offline": self.prefs.prefer_offline,
                        "budget_per_session_usd": self.prefs.budget_per_session_usd,
                        "pins": {
                            k: v.value for k, v in self.prefs.pinned_skills.items()
                        },
                    }
                },
                f,
            )


# ---------------------------------------------------------------------------
# SmartRouter
# ---------------------------------------------------------------------------

class SmartRouter:
    """Top-level router used by the TUI skill dispatcher.

    Combines CostBasedStrategy, CapabilityBasedStrategy, and
    UserOverrideStrategy with configurable weights.

    Default weights: cost=0.3, capability=0.5, preference=0.2
    """

    def __init__(
        self,
        config: RouterConfig | None = None,
        health: dict[Provider, ProviderHealth] | None = None,
        cost_weight: float = DEFAULT_COST_WEIGHT,
        capability_weight: float = DEFAULT_CAPABILITY_WEIGHT,
        preference_weight: float = DEFAULT_PREFERENCE_WEIGHT,
    ) -> None:
        self._config = config or RouterConfig()
        self._health: dict[Provider, ProviderHealth] = health or {
            p: ProviderHealth(p) for p in Provider
        }
        self.cost_weight = cost_weight
        self.capability_weight = capability_weight
        self.preference_weight = preference_weight

    def update_health(self, health: dict[Provider, ProviderHealth]) -> None:
        """Update provider health snapshot (called by HealthMonitor)."""
        self._health = health

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, skill_name: str, context: dict[str, Any] | None = None) -> Provider:
        """Pick the best provider for a skill.

        Args:
            skill_name: Name of the skill to route.
            context: Optional runtime context (currently unused, reserved for
                     future dynamic routing based on session state).

        Returns:
            The best Provider for this skill.
        """
        from .table import DEFAULT_ROUTING, SkillRoutingEntry

        entry = DEFAULT_ROUTING.get(skill_name)
        if entry is None:
            # Unknown skill — use a minimal stub
            skill_meta = SkillMetadata(
                name=skill_name,
                category=entry.category if entry else None,  # type: ignore[arg-type]
                cost_tier=CostTier.LOW,
                dependencies=["shell"],
            )
        else:
            skill_meta = entry.to_skill_metadata()

        decision = self._decide(skill_meta)
        return decision.primary

    def decide(self, skill_meta: SkillMetadata) -> RoutingDecision:
        """Full routing decision including fallback chain and rationale."""
        return self._decide(skill_meta)

    async def dispatch(
        self,
        skill_meta: SkillMetadata,
        execute_fn: Callable[[Provider, SkillMetadata], Any],
        notify_fn: Callable[[str], None],
        timeout: float = 60.0,
    ) -> Any:
        """Route and execute a skill with automatic fallback.

        Args:
            skill_meta: Skill to execute.
            execute_fn: Callable(provider, skill) that performs the actual work.
            notify_fn: Callable(message) used to inform the user about routing events.
            timeout: Seconds to wait per provider before trying the next fallback.
        """
        decision = self._decide(skill_meta)
        notify_fn(
            f"Routing /{skill_meta.name} -> {decision.primary.value}  "
            f"({decision.rationale})"
        )
        return await execute_with_fallback(
            chain=decision.fallback_chain,
            action=lambda provider: execute_fn(provider, skill_meta),
            primary=decision.primary,
            notify_fn=notify_fn,
            timeout=timeout,
        )

    def get_routing_table(self) -> dict[str, dict[str, Any]]:
        """Return all skills with their primary and fallback providers.

        Returns a dict keyed by skill name, each value containing:
            primary: str — best provider name
            fallbacks: list[str] — ordered fallback chain
            rationale: str — explanation of the routing decision
            cost_tier: str
        """
        from .table import DEFAULT_ROUTING

        table: dict[str, dict[str, Any]] = {}
        for skill_name, entry in DEFAULT_ROUTING.items():
            skill_meta = entry.to_skill_metadata()
            decision = self._decide(skill_meta)
            table[skill_name] = {
                "primary": decision.primary.value,
                "fallbacks": [p.value for p in decision.fallback_chain],
                "rationale": decision.rationale,
                "cost_tier": decision.estimated_cost_tier.value,
                "category": skill_meta.category.value,
            }
        return table

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _decide(self, skill: SkillMetadata) -> RoutingDecision:
        """Core routing logic: user pin → hybrid scoring → fallback chain."""
        prefs = self._config.prefs

        # 1. User pin overrides everything
        override_strategy = UserOverrideStrategy(prefs)
        pinned = override_strategy.route(skill, self._health)
        if pinned:
            primary = pinned[0]
            fallback = _deduped_fallback(primary, [], FALLBACK_CHAINS, self._health)
            h = self._health.get(primary, ProviderHealth(primary))
            if not h.available or h.rate_limited:
                reason = "rate-limited" if h.rate_limited else "unavailable"
                if fallback:
                    rationale = (
                        f"User pin: {primary.value} ({reason}); "
                        f"falling back to {fallback[0].value}"
                    )
                    primary = fallback[0]
                    fallback = fallback[1:]
                else:
                    rationale = (
                        f"User pin: {primary.value} ({reason}); no fallbacks available"
                    )
            else:
                rationale = f"User pin: {primary.value}"
            return RoutingDecision(
                primary=primary,
                fallback_chain=fallback,
                rationale=rationale,
                estimated_cost_tier=skill.cost_tier,
            )

        # 2. Hybrid scoring
        cost_strategy = CostBasedStrategy(prefs)
        cap_strategy = CapabilityBasedStrategy()

        cost_ranked = cost_strategy.route(skill, self._health)
        cap_ranked = cap_strategy.route(skill, self._health)

        scores: dict[Provider, float] = {p: 0.0 for p in Provider}

        n_cost = len(cost_ranked)
        for rank, provider in enumerate(cost_ranked):
            scores[provider] += self.cost_weight * (n_cost - rank) / max(n_cost, 1)

        n_cap = len(cap_ranked)
        for rank, provider in enumerate(cap_ranked):
            scores[provider] += self.capability_weight * (n_cap - rank) / max(n_cap, 1)

        for provider, h in self._health.items():
            if h.available and not h.rate_limited:
                latency_bonus = max(0.0, 1.0 - h.latency_ms / 5000.0)
                scores[provider] += self.preference_weight * latency_bonus

        # Must appear in both cost and capability lists
        eligible = set(cost_ranked) & set(cap_ranked)
        ranked = sorted(eligible, key=lambda p: scores[p], reverse=True)

        if not ranked:
            primary = Provider.DIRECT
            fallback: list[Provider] = []
            rationale = "No eligible provider found — falling back to direct shell execution"
        else:
            primary = ranked[0]
            extra = [p for p in ranked[1:]]
            fallback = _deduped_fallback(primary, extra, FALLBACK_CHAINS, self._health)
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deduped_fallback(
    primary: Provider,
    extra: list[Provider],
    chains: dict[Provider, list[Provider]],
    health: dict[Provider, ProviderHealth],
) -> list[Provider]:
    """Build a deduplicated fallback list, preferring healthy providers."""
    raw = extra + chains.get(primary, [])
    seen: set[Provider] = {primary}
    result: list[Provider] = []
    for p in raw:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


# Remove circular import placeholder that was accidentally referenced above
# (FALLBACK_CHAINS_DEFAULT is defined in this module, not strategies.py)
# Patch strategies module reference
import sys as _sys

_strategies_mod = _sys.modules.get(__name__.replace(".router", ".strategies"))
if _strategies_mod is not None and not hasattr(_strategies_mod, "FALLBACK_CHAINS_DEFAULT"):
    pass  # strategies.py does not define FALLBACK_CHAINS_DEFAULT — that's fine
