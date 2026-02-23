"""Narration generator that orchestrates multiple providers in order."""

from __future__ import annotations

import logging
import time
from typing import Iterable

from .providers import (
    BaseNarrator,
    MinimaxNarrator,
    OllamaNarrator,
    PassthroughNarrator,
)
from .claude_code import ClaudeCodeNarrator
from .template import TemplateNarrator

logger = logging.getLogger("multikanal.narration.generator")


class NarrationGenerator:
    """Tries providers in order until one returns narration."""

    def __init__(self, providers: Iterable[BaseNarrator]):
        self.providers = list(providers)
        self.last_result: dict = {}

    @classmethod
    def from_config(cls, narr_cfg: dict) -> "NarrationGenerator":
        providers_cfg = narr_cfg.get("providers") or []
        providers: list[BaseNarrator] = []

        if providers_cfg:
            for p in providers_cfg:
                if not isinstance(p, dict) or not p.get("enabled", True):
                    continue
                name = p.get("name")
                if name == "template":
                    providers.append(TemplateNarrator())
                elif name == "claude_code":
                    providers.append(
                        ClaudeCodeNarrator(
                            claude_path=p.get(
                                "claude_path", "/home/smlflg/.local/bin/claude"
                            ),
                            max_words=narr_cfg.get("max_output_words", 80),
                            timeout=p.get("timeout_seconds", 30),
                        )
                    )
                elif name == "minimax":
                    providers.append(
                        MinimaxNarrator(
                            api_key=p.get("api_key"),
                            endpoint=p.get("endpoint", ""),
                            model=p.get("model", ""),
                            temperature=p.get("temperature", 0.6),
                            max_tokens=p.get(
                                "max_tokens", narr_cfg.get("max_output_words", 80) * 3
                            ),
                            timeout=p.get(
                                "timeout_seconds", narr_cfg.get("timeout_seconds", 10)
                            ),
                        )
                    )
                elif name == "ollama":
                    providers.append(
                        OllamaNarrator(
                            ollama_url=p.get(
                                "ollama_url",
                                narr_cfg.get("ollama_url", "http://localhost:11434"),
                            ),
                            models=p.get("models", narr_cfg.get("models", [])),
                            max_words=narr_cfg.get("max_output_words", 80),
                            timeout=p.get(
                                "timeout_seconds", narr_cfg.get("timeout_seconds", 10)
                            ),
                        )
                    )
                elif name == "passthrough":
                    providers.append(
                        PassthroughNarrator(
                            max_words=narr_cfg.get("max_output_words", 80),
                        )
                    )
        # Legacy fallback if providers not set
        if not providers:
            providers.append(
                OllamaNarrator(
                    ollama_url=narr_cfg.get("ollama_url", "http://localhost:11434"),
                    models=narr_cfg.get("models", []),
                    max_words=narr_cfg.get("max_output_words", 80),
                    timeout=narr_cfg.get("timeout_seconds", 10),
                )
            )
            providers.append(
                PassthroughNarrator(max_words=narr_cfg.get("max_output_words", 80))
            )

        return cls(providers)

    def generate(self, text: str, system_prompt: str = "", language: str = "", session_id: str = "") -> str:
        if not text.strip():
            return ""

        for provider in self.providers:
            narration = ""
            t0 = time.monotonic()
            try:
                narration = provider.generate(text, system_prompt, language, session_id=session_id)
            except Exception as exc:  # noqa: BLE001
                logger.debug("provider %s raised: %s", provider.name, exc)
            if narration:
                latency_ms = int((time.monotonic() - t0) * 1000)
                self.last_result = {
                    "provider": provider.name,
                    "latency_ms": latency_ms,
                }
                logger.info("narration generated via provider=%s", provider.name)
                return narration

        logger.warning("all providers failed to generate narration")
        return ""

    def reset_history(self, session_id: str = "") -> None:
        for provider in self.providers:
            if hasattr(provider, "clear_history"):
                provider.clear_history(session_id)

    def health_map(self) -> dict[str, bool]:
        status: dict[str, bool] = {}
        for provider in self.providers:
            ok = False
            try:
                ok = provider.check_health()
            except Exception:  # noqa: BLE001
                ok = False
            status[provider.name] = ok
        return status
