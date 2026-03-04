"""AppCore — central orchestrator wiring all TUI subsystems together.

Startup order:
  1. State layer  (SQLite DB init)
  2. Providers    (health-check each)
  3. Router       (needs providers; optional — graceful fallback)
  4. Skills       (discover from config.skills_dirs)
  5. Event bus    (publish/subscribe backbone)
  6. Voice        (optional)
  7. ADHS engine  (optional)

Usage:
    core = AppCore(config)
    await core.startup()
    async for chunk in core.invoke_skill("chef", "add tests"):
        print(chunk)
    await core.shutdown()
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Any

from tui.logging_config import setup_logging, get_logger
from tui.di import Container, get_container
from tui.providers.base import BaseProvider
from tui.providers.claude import ClaudeCodeProvider
from tui.providers.opencode import OpenCodeProvider
from tui.providers.codex import CodexProvider
from tui.state.database import init_db, close_db
from tui.state.repository import SessionRepo, MessageRepo, CostRepo

# Optional imports — graceful if the module is not yet built
try:
    from tui.skills.engine import SkillEngine  # type: ignore[import]
except ImportError:
    SkillEngine = None  # type: ignore[assignment,misc]

try:
    from tui.router.smart_router import SmartRouter  # type: ignore[import]
except ImportError:
    SmartRouter = None  # type: ignore[assignment,misc]

try:
    from tui.voice.manager import VoiceManager  # type: ignore[import]
except ImportError:
    VoiceManager = None  # type: ignore[assignment,misc]

try:
    from tui.adhs.session import ADHSSessionManager  # type: ignore[import]
except ImportError:
    ADHSSessionManager = None  # type: ignore[assignment,misc]


log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Simple in-process event bus
# ---------------------------------------------------------------------------

class EventBus:
    """Minimal publish/subscribe event bus.

    Handlers are registered per event-type string and called synchronously.
    Async handlers are scheduled on the running event loop.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list] = {}

    def subscribe(self, event_type: str, handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: str, handler) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event_type: str, payload: Any = None) -> None:
        for handler in list(self._handlers.get(event_type, [])):
            try:
                if asyncio.iscoroutinefunction(handler):
                    loop = asyncio.get_event_loop()
                    loop.create_task(handler(event_type, payload))
                else:
                    handler(event_type, payload)
            except Exception as exc:
                log.warning("EventBus handler error [%s]: %s", event_type, exc)


# ---------------------------------------------------------------------------
# Config dataclass (minimal — enough for AppCore to function)
# ---------------------------------------------------------------------------

@dataclass
class Config:
    """Runtime configuration passed to AppCore."""

    db_path: Path = field(
        default_factory=lambda: Path.home() / ".local" / "share" / "myaigame" / "state.db"
    )
    skills_dirs: list[Path] = field(default_factory=list)
    default_provider: str = "claude-code"
    debug: bool = False
    voice_enabled: bool = False
    adhs_enabled: bool = True

    @classmethod
    def default(cls) -> "Config":
        """Return a Config with sensible defaults."""
        skills_root = Path.home() / "Projekte" / "MyAIGame" / "portable" / "skills"
        dirs = [skills_root] if skills_root.exists() else []
        return cls(skills_dirs=dirs)


# ---------------------------------------------------------------------------
# AppCore
# ---------------------------------------------------------------------------

class AppCore:
    """Central orchestrator wiring all TUI subsystems together."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.event_bus = EventBus()
        self.providers: dict[str, BaseProvider] = {}
        self.router: Any | None = None        # SmartRouter when available
        self.skills: Any | None = None        # SkillEngine when available
        self.voice: Any | None = None         # VoiceManager when available
        self.adhs: Any | None = None          # ADHSSessionManager when available
        self._active_session_id: str | None = None
        self._container: Container = get_container()
        self._started = False

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    async def startup(self) -> None:
        """Initialize all subsystems in the correct order."""
        if self._started:
            return
        self._started = True

        setup_logging(debug=self.config.debug)
        log.info("AppCore starting up …")

        # 1. State layer
        await asyncio.to_thread(init_db)
        log.info("State layer ready (SQLite)")

        # Register state helpers in DI container
        self._container.register_instance("session_repo", SessionRepo)
        self._container.register_instance("message_repo", MessageRepo)
        self._container.register_instance("cost_repo", CostRepo)

        # 2. Providers
        self._init_providers()

        # 3. Router (optional)
        if SmartRouter is not None:
            try:
                self.router = SmartRouter(providers=self.providers)
                log.info("SmartRouter initialized with %d providers", len(self.providers))
                self._container.register_instance("router", self.router)
            except Exception as exc:
                log.warning("SmartRouter init failed: %s", exc)

        # 4. Skills
        if SkillEngine is not None:
            try:
                self.skills = SkillEngine()
                for skills_dir in self.config.skills_dirs:
                    self.skills.discover_skills(str(skills_dir))
                skill_count = len(self.skills.list_skills())
                log.info("SkillEngine: %d skills loaded", skill_count)
                self._container.register_instance("skills", self.skills)
                self.event_bus.publish("skills.loaded", {"count": skill_count})
            except Exception as exc:
                log.warning("SkillEngine init failed: %s", exc)
        else:
            log.info("SkillEngine not available (module not yet built)")

        # 5. Event bus is already ready — register it in DI
        self._container.register_instance("event_bus", self.event_bus)

        # 6. Voice (optional)
        if self.config.voice_enabled and VoiceManager is not None:
            try:
                self.voice = VoiceManager()
                await self.voice.connect()
                log.info("VoiceManager connected")
                self._container.register_instance("voice", self.voice)
            except Exception as exc:
                log.warning("Voice unavailable: %s", exc)
                self.voice = None

        # 7. ADHS engine (optional)
        if self.config.adhs_enabled and ADHSSessionManager is not None:
            try:
                self.adhs = ADHSSessionManager(event_bus=self.event_bus)
                log.info("ADHSSessionManager ready")
                self._container.register_instance("adhs", self.adhs)
            except Exception as exc:
                log.warning("ADHS engine init failed: %s", exc)
                self.adhs = None
        else:
            log.info("ADHS engine not available (module not yet built)")

        # Create a default session
        self._active_session_id = await asyncio.to_thread(
            lambda: SessionRepo.create(
                goal="TUI Session",
                provider=self.config.default_provider,
            ).id
        )
        log.info("AppCore startup complete. Session: %s", self._active_session_id)
        self.event_bus.publish("core.started", {"session_id": self._active_session_id})

    # ------------------------------------------------------------------
    # Provider initialization
    # ------------------------------------------------------------------

    def _init_providers(self) -> None:
        """Instantiate and health-check all providers."""
        candidates: list[BaseProvider] = [
            ClaudeCodeProvider(),
            OpenCodeProvider(),
            CodexProvider(),
        ]
        for provider in candidates:
            try:
                status = provider.health_check()
                self.providers[provider.provider_id] = provider
                health_str = "healthy" if status.get("healthy") else "unhealthy"
                log.info("Provider %s: %s (model=%s)", provider.provider_id, health_str, status.get("model"))
            except Exception as exc:
                log.warning("Provider %s health check failed: %s", provider.provider_id, exc)

        if not self.providers:
            log.error("No providers available — TUI will run in degraded mode")

        # Register each provider in DI
        for pid, prov in self.providers.items():
            self._container.register_instance(f"provider.{pid}", prov)

        log.info("Providers ready: %s", list(self.providers.keys()))

    # ------------------------------------------------------------------
    # Skill invocation pipeline
    # ------------------------------------------------------------------

    async def invoke_skill(self, name: str, args: str = "") -> AsyncIterator[str]:
        """Full pipeline: resolve skill → route → execute → track → emit events.

        Yields streamed response chunks as strings.
        Falls back gracefully when optional subsystems are missing.
        """
        start_ms = int(time.monotonic() * 1000)
        session_id = self._active_session_id or "unknown"

        self.event_bus.publish("skill.invoke.start", {"name": name, "args": args})
        log.info("Invoking skill '%s' args=%r", name, args)

        # Resolve skill metadata (if engine available)
        skill_meta: dict = {}
        if self.skills is not None:
            skill_meta = self.skills.get_skill(name) or {}

        # Choose provider
        provider = self._resolve_provider(skill_meta)
        if provider is None:
            yield f"[error] No provider available for skill '{name}'"
            return

        # Build prompt
        prompt = f"[SKILL: {name}] {args or skill_meta.get('description', '')}"

        # Execute — providers are currently sync; run in thread to stay non-blocking
        try:
            response = await asyncio.to_thread(provider.send_prompt, prompt)
        except Exception as exc:
            log.error("Provider error during skill '%s': %s", name, exc)
            self.event_bus.publish("skill.invoke.error", {"name": name, "error": str(exc)})
            yield f"[error] {exc}"
            return

        content: str = response.get("content", "")
        tokens_in: int = response.get("tokens", 0)
        cost: float = response.get("cost", 0.0)
        model: str = response.get("model", "unknown")
        duration_ms = int(time.monotonic() * 1000) - start_ms

        # Persist cost event
        if session_id != "unknown":
            try:
                await asyncio.to_thread(
                    CostRepo.add_event,
                    session_id, provider.provider_id, model,
                    tokens_in, 0, cost, "skill",
                )
            except Exception as exc:
                log.warning("Failed to persist cost event: %s", exc)

        # Emit completion event
        self.event_bus.publish("skill.invoke.complete", {
            "name": name,
            "provider": provider.provider_id,
            "cost": cost,
            "duration_ms": duration_ms,
        })
        log.info("Skill '%s' done in %dms cost=$%.4f", name, duration_ms, cost)

        # Yield content as a single chunk (providers are sync/batch for now)
        yield content

    def _resolve_provider(self, skill_meta: dict) -> BaseProvider | None:
        """Choose the best provider for a given skill.

        Uses the router if available, otherwise falls back to the configured
        default provider, then to the first healthy provider.
        """
        if self.router is not None:
            try:
                pid = self.router.select(skill_meta)
                if pid and pid in self.providers:
                    return self.providers[pid]
            except Exception as exc:
                log.warning("Router selection failed: %s", exc)

        # Fallback: configured default
        if self.config.default_provider in self.providers:
            return self.providers[self.config.default_provider]

        # Last resort: first available
        return next(iter(self.providers.values()), None)

    # ------------------------------------------------------------------
    # Chat (non-skill messages)
    # ------------------------------------------------------------------

    async def send_message(self, text: str) -> dict:
        """Send a plain chat message to the active provider.

        Returns the provider response dict.
        """
        provider = self._resolve_provider({})
        if provider is None:
            return {"content": "[error] No provider available", "cost": 0.0, "tokens": 0}

        response = await asyncio.to_thread(provider.send_prompt, text)

        session_id = self._active_session_id or "unknown"
        if session_id != "unknown":
            try:
                await asyncio.to_thread(
                    MessageRepo.add,
                    session_id, "assistant", response.get("content", ""),
                    response.get("tokens", 0), 0, response.get("cost", 0.0),
                )
                await asyncio.to_thread(
                    CostRepo.add_event,
                    session_id, provider.provider_id, response.get("model", "unknown"),
                    response.get("tokens", 0), 0, response.get("cost", 0.0), "message",
                )
            except Exception as exc:
                log.warning("Failed to persist message: %s", exc)

        self.event_bus.publish("message.received", {"provider": provider.provider_id})
        return response

    # ------------------------------------------------------------------
    # Provider management
    # ------------------------------------------------------------------

    def get_provider(self, provider_id: str) -> BaseProvider | None:
        """Return a specific provider by ID."""
        return self.providers.get(provider_id)

    def set_active_provider(self, provider_id: str) -> bool:
        """Switch the default provider. Returns True on success."""
        if provider_id not in self.providers:
            log.warning("Unknown provider: %s", provider_id)
            return False
        self.config.default_provider = provider_id
        self.event_bus.publish("provider.changed", {"provider_id": provider_id})
        log.info("Active provider changed to '%s'", provider_id)
        return True

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    async def shutdown(self) -> None:
        """Save state, export costs, clean up connections."""
        if not self._started:
            return

        log.info("AppCore shutting down …")
        self.event_bus.publish("core.shutdown", {})

        # Close active session
        if self._active_session_id:
            try:
                from datetime import datetime
                await asyncio.to_thread(
                    SessionRepo.update,
                    self._active_session_id,
                    status="completed",
                    ended_at=datetime.utcnow(),
                )
                log.info("Session %s closed", self._active_session_id)
            except Exception as exc:
                log.warning("Failed to close session: %s", exc)

        # Disconnect voice
        if self.voice is not None:
            try:
                await self.voice.disconnect()
            except Exception as exc:
                log.warning("Voice disconnect error: %s", exc)

        # Close DB
        try:
            await asyncio.to_thread(close_db)
        except Exception as exc:
            log.warning("DB close error: %s", exc)

        self._started = False
        log.info("AppCore shutdown complete")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "AppCore":
        await self.startup()
        return self

    async def __aexit__(self, *_) -> None:
        await self.shutdown()
