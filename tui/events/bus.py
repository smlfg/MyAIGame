"""
EventBus — dispatches events to registered plugin handlers.

Design goals (per TUI_EVENTS.md §4.5 / §7):
- Error isolation: one crashing handler NEVER blocks others or the agent
- Timeout: every handler gets HANDLER_TIMEOUT seconds (default 10s)
- Auto-disable: plugin disabled after MAX_CRASHES crashes in one session
- Async support: handlers that are coroutines are awaited via asyncio
- Logging: every emit is logged at DEBUG level
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import threading
from pathlib import Path
from typing import Any

log = logging.getLogger("tui.events")

HANDLER_TIMEOUT = 10   # seconds per handler
MAX_CRASHES = 3


class EventBus:
    """Dispatches events to all handlers registered on a PluginRegistry."""

    def __init__(self, registry):
        self._registry = registry
        self._crash_counts: dict[str, int] = {}   # plugin_key -> crash count
        self._disabled: set[str] = set()           # plugin_keys that are off

    # ------------------------------------------------------------------
    # Plugin loading
    # ------------------------------------------------------------------

    def load_plugins(self, directory: Path) -> None:
        """Discover and import all .py plugin files in *directory*."""
        import importlib.util

        if not directory.exists():
            log.info("Plugin directory not found: %s", directory)
            return

        for py_file in sorted(directory.glob("*.py")):
            name = py_file.stem
            if name.startswith("_"):
                continue
            self._import_plugin(name, py_file)

    def _import_plugin(self, name: str, path: Path) -> bool:
        """Import a single plugin file. Returns True on success."""
        import importlib.util

        try:
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)   # type: ignore[union-attr]
            log.info("Loaded plugin: %s (%s)", name, path)
            return True
        except Exception as exc:
            log.error("Failed to load plugin %s: %s", name, exc)
            return False

    # ------------------------------------------------------------------
    # Emitting events
    # ------------------------------------------------------------------

    def emit(self, event_type: str, event: Any) -> list[dict]:
        """Emit an event synchronously. Returns non-None handler results.

        For async handlers, the current running event loop is used if
        available; otherwise a new one is created for this call.
        """
        handlers = self._registry.handlers_for(event_type)
        log.debug("emit %s → %d handler(s)", event_type, len(handlers))

        responses: list[dict] = []
        for handler in handlers:
            key = _handler_key(handler)
            if key in self._disabled:
                log.debug("Skipping disabled plugin handler: %s", key)
                continue

            try:
                result = self._run(handler, event)
                if result is not None:
                    if isinstance(result, dict):
                        responses.append(result)
                    else:
                        log.warning("Handler %s returned non-dict: %r", key, result)
            except TimeoutError:
                log.warning("Handler %s timed out (>%ds) on %s", key, HANDLER_TIMEOUT, event_type)
                self._record_crash(key)
            except Exception as exc:
                log.error("Handler %s crashed on %s: %s", key, event_type, exc, exc_info=True)
                self._record_crash(key)

        return responses

    async def emit_async(self, event_type: str, event: Any) -> list[dict]:
        """Async variant of emit — awaits coroutine handlers natively."""
        handlers = self._registry.handlers_for(event_type)
        log.debug("emit_async %s → %d handler(s)", event_type, len(handlers))

        responses: list[dict] = []
        for handler in handlers:
            key = _handler_key(handler)
            if key in self._disabled:
                continue

            try:
                if inspect.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(handler(event), timeout=HANDLER_TIMEOUT)
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, handler, event),
                        timeout=HANDLER_TIMEOUT,
                    )
                if result is not None:
                    if isinstance(result, dict):
                        responses.append(result)
                    else:
                        log.warning("Handler %s returned non-dict: %r", key, result)
            except asyncio.TimeoutError:
                log.warning("Handler %s timed out (>%ds) on %s", key, HANDLER_TIMEOUT, event_type)
                self._record_crash(key)
            except Exception as exc:
                log.error("Handler %s crashed on %s: %s", key, event_type, exc, exc_info=True)
                self._record_crash(key)

        return responses

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run(self, handler, event: Any, timeout: float = HANDLER_TIMEOUT) -> Any:
        """Run a handler in a daemon thread with timeout.

        Coroutines are run via asyncio.run() inside the thread.
        Raises TimeoutError or re-raises handler exceptions.
        """
        result_box: list[Any] = [None]
        error_box: list[BaseException | None] = [None]

        def _target():
            try:
                if inspect.iscoroutinefunction(handler):
                    result_box[0] = asyncio.run(handler(event))
                else:
                    result_box[0] = handler(event)
            except BaseException as exc:  # noqa: BLE001
                error_box[0] = exc

        thread = threading.Thread(target=_target, daemon=True, name=f"tui-handler-{_handler_key(handler)}")
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            raise TimeoutError(f"{_handler_key(handler)} exceeded {timeout}s")
        if error_box[0] is not None:
            raise error_box[0]
        return result_box[0]

    def _record_crash(self, key: str) -> None:
        """Track crashes per handler key. Auto-disable after MAX_CRASHES."""
        self._crash_counts[key] = self._crash_counts.get(key, 0) + 1
        count = self._crash_counts[key]
        if count >= MAX_CRASHES:
            self._disabled.add(key)
            log.warning(
                "Plugin handler '%s' disabled after %d crash(es) in this session.",
                key, MAX_CRASHES,
            )

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    @property
    def disabled_plugins(self) -> frozenset[str]:
        return frozenset(self._disabled)

    @property
    def crash_counts(self) -> dict[str, int]:
        return dict(self._crash_counts)


def _handler_key(handler) -> str:
    """Stable human-readable key for a handler function."""
    module = getattr(handler, "__module__", None) or "unknown"
    qualname = getattr(handler, "__qualname__", None) or repr(handler)
    return f"{module}.{qualname}"
