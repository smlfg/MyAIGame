"""Minimal dependency injection container for MyAIGame TUI.

Usage:
    container = Container()
    container.register(Config, lambda: Config.load())
    cfg = container.get(Config)   # factory called once, result cached
"""

from __future__ import annotations

from typing import Any, Callable, Type, TypeVar

T = TypeVar("T")


class Container:
    """Lightweight singleton registry.

    Factories are called lazily on first get() and the result is cached.
    Supports registration by type *or* by string key.
    """

    def __init__(self) -> None:
        self._factories: dict[Any, Callable[[], Any]] = {}
        self._instances: dict[Any, Any] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, key: type | str, factory: Callable[[], Any]) -> None:
        """Register a factory for *key*.

        The factory must be a zero-argument callable that returns the instance.
        Re-registering a key clears any cached instance so the new factory
        is used on the next get().
        """
        self._factories[key] = factory
        self._instances.pop(key, None)

    def register_instance(self, key: type | str, instance: Any) -> None:
        """Register a pre-built instance directly (no factory needed)."""
        self._instances[key] = instance
        self._factories.pop(key, None)

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def get(self, key: type[T] | str) -> T:
        """Return the singleton instance for *key*, building it if necessary.

        Raises KeyError if nothing is registered under *key*.
        """
        if key not in self._instances:
            if key not in self._factories:
                raise KeyError(f"No registration found for {key!r}")
            self._instances[key] = self._factories[key]()
        return self._instances[key]  # type: ignore[return-value]

    def has(self, key: type | str) -> bool:
        """Return True if *key* has a registered factory or cached instance."""
        return key in self._factories or key in self._instances

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def registered_keys(self) -> list:
        """All keys that have a factory or cached instance."""
        return list(set(self._factories) | set(self._instances))

    def __repr__(self) -> str:
        return (
            f"<Container keys={self.registered_keys()}>"
        )


# Module-level default container — AppCore and CLI share this instance.
_default_container: Container | None = None


def get_container() -> Container:
    """Return (or create) the process-wide default Container."""
    global _default_container
    if _default_container is None:
        _default_container = Container()
    return _default_container


def reset_container() -> None:
    """Reset the default container (useful in tests)."""
    global _default_container
    _default_container = None
