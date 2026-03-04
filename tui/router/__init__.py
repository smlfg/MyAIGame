"""Smart Router package for MyAIGame TUI.

Automatically picks the best backend per skill invocation based on
cost, capability, availability, and user preferences.
"""

from .strategies import (
    RoutingStrategy,
    CostBasedStrategy,
    CapabilityBasedStrategy,
    UserOverrideStrategy,
    Provider,
    CostTier,
    Category,
    SkillMetadata,
    ProviderHealth,
    UserPreferences,
    RoutingDecision,
    PROVIDER_COST_RANK,
    COST_TIER_CEILING,
    PROVIDER_CAPABILITIES,
)
from .router import SmartRouter, RouterConfig
from .fallback import FallbackChain, execute_with_fallback, RoutingError
from .table import DEFAULT_ROUTING, SkillRoutingEntry

__all__ = [
    # Domain types
    "Provider",
    "CostTier",
    "Category",
    "SkillMetadata",
    "ProviderHealth",
    "UserPreferences",
    "RoutingDecision",
    # Constants
    "PROVIDER_COST_RANK",
    "COST_TIER_CEILING",
    "PROVIDER_CAPABILITIES",
    "DEFAULT_ROUTING",
    # Strategies
    "RoutingStrategy",
    "CostBasedStrategy",
    "CapabilityBasedStrategy",
    "UserOverrideStrategy",
    # Router
    "SmartRouter",
    "RouterConfig",
    # Fallback
    "FallbackChain",
    "execute_with_fallback",
    "RoutingError",
    # Table
    "SkillRoutingEntry",
]
