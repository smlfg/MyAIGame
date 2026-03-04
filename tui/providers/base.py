"""Abstract base provider for AI backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract base class for all AI provider backends.

    Concrete providers implement this interface so the TUI can switch
    between Claude Code, OpenCode, and Codex without changing application logic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Machine-readable provider identifier."""

    @abstractmethod
    def send_prompt(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Send a prompt and return the response.

        Returns a dict with at minimum:
            content (str): The response text
            tokens (int): Tokens used
            cost (float): Estimated cost in USD
            model (str): Model used
        """

    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        """Return provider capabilities.

        Returns a dict describing what the provider supports:
            skills (bool): Supports skill invocation
            async_sessions (bool): Supports async sessions
            multi_agent (bool): Supports multi-agent orchestration
            voice (bool): Supports voice I/O
            file_ops (bool): Supports file operations
            web_search (bool): Has web search capability
            models (list[str]): Available models
        """

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Check if the provider is available.

        Returns a dict with:
            healthy (bool): Whether the provider is reachable
            model (str): Current active model
            latency_ms (int): Last ping latency, or -1 if not checked
            error (str | None): Error message if unhealthy
        """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.provider_id!r}>"
