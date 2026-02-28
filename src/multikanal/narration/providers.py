"""Narration provider interfaces and implementations (Minimax, Ollama)."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from collections import deque
from typing import Iterable

import re

import httpx

logger = logging.getLogger("multikanal.narration.providers")

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_MARKDOWN_RE = re.compile(r"\*{1,3}|#{1,6}\s?|`{1,3}")  # strip bold/italic/headers/code


def _clean_for_tts(text: str) -> str:
    """Strip think-tags and markdown formatting for clean TTS output."""
    text = _THINK_RE.sub("", text)
    text = _MARKDOWN_RE.sub("", text)
    # Collapse multiple newlines into single space
    text = re.sub(r"\n+", " ", text)
    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


class BaseNarrator(ABC):
    """Abstract narration provider."""

    name: str

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate(
        self, text: str, system_prompt: str = "", language: str = "", session_id: str = ""
    ) -> str: ...

    @abstractmethod
    def check_health(self) -> bool: ...


class MinimaxNarrator(BaseNarrator):
    def __init__(
        self,
        api_key: str | None,
        endpoint: str,
        model: str,
        temperature: float = 0.6,
        max_tokens: int = 240,
        timeout: int = 6,
    ):
        super().__init__("minimax")
        self.api_key = api_key or ""
        self.endpoint = endpoint
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._histories: dict[str, deque] = {}
        self._history_maxlen: int = 6  # max message pairs per session
        self._last_active: dict[str, float] = {}
        self._session_ttl: float = 4 * 3600  # purge after 4h inactivity

    def _purge_old_sessions(self) -> None:
        now = time.time()
        expired = [k for k, t in self._last_active.items() if now - t > self._session_ttl]
        for k in expired:
            self._histories.pop(k, None)
            self._last_active.pop(k, None)

    def clear_history(self, session_id: str = "") -> None:
        if session_id:
            self._histories.pop(session_id, None)
            self._last_active.pop(session_id, None)
        else:
            self._histories.clear()
            self._last_active.clear()

    def generate(self, text: str, system_prompt: str = "", language: str = "", session_id: str = "") -> str:
        if not self.api_key or not self.endpoint or not self.model or not text.strip():
            return ""

        key = session_id or "default"
        self._purge_old_sessions()
        self._last_active[key] = time.time()
        history = self._histories.setdefault(key, deque(maxlen=self._history_maxlen * 2))

        messages = [{"role": "system", "content": system_prompt or ""}]
        messages.extend(list(history))
        messages.append({"role": "user", "content": text})

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages,
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            resp = httpx.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            # Minimax responses can vary; try common shapes
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                # Various possible fields
                msg = choice.get("message") or choice.get("delta") or {}
                content = msg.get("content") or msg.get("text") or ""
                if not content and "messages" in choice:
                    msgs = choice.get("messages") or []
                    if isinstance(msgs, list) and msgs:
                        content = msgs[0].get("content") or msgs[0].get("text") or ""
                if not content and "output_text" in choice:
                    content = choice["output_text"]
                if isinstance(content, list):
                    content = "".join(
                        c.get("text", "") if isinstance(c, dict) else str(c)
                        for c in content
                    )
                if isinstance(content, str) and content.strip():
                    content = _clean_for_tts(content)
                    if content:
                        history.append({"role": "user", "content": text})
                        history.append({"role": "assistant", "content": content})
                        return content

            # Fallback: try top-level text/content
            for key in ("text", "content", "output", "output_text"):
                if key in data and isinstance(data[key], str) and data[key].strip():
                    cleaned = _clean_for_tts(data[key])
                    if cleaned:
                        return cleaned
        except Exception as exc:  # noqa: BLE001
            logger.warning("minimax failed: %s", exc)
            return ""

        logger.warning("minimax returned empty response for %d chars input", len(text))
        return ""

    def check_health(self) -> bool:
        if not self.api_key or not self.endpoint:
            return False
        try:
            # Use /v1/models endpoint for health check instead of chat endpoint
            base = self.endpoint.rsplit("/v1/", 1)[0] + "/v1/models"
            resp = httpx.get(
                base,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=3,
            )
            return resp.status_code < 500
        except Exception:  # noqa: BLE001
            return False


class OllamaNarrator(BaseNarrator):
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        models: Iterable[str] | None = None,
        max_words: int = 80,
        timeout: int = 10,
    ):
        super().__init__("ollama")
        self.ollama_url = ollama_url.rstrip("/")
        self.models = list(models or ["llama3.1:8b", "phi4", "mistral-nemo"])
        self.max_words = max_words
        self.timeout = timeout

    def generate(self, text: str, system_prompt: str = "", language: str = "", session_id: str = "") -> str:
        if not text.strip():
            return ""

        user_prompt = (
            f"Agent-Ausgabe:\n\n{text}\n\n"
            f"Erstelle eine Audio-Erklärung (maximal {self.max_words} Wörter)."
        )

        for model in self.models:
            try:
                result = self._call_ollama(model, system_prompt, user_prompt)
                if result:
                    logger.info(
                        "narration generated with model=%s (%d chars)",
                        model,
                        len(result),
                    )
                    return result
            except Exception as exc:  # noqa: BLE001
                logger.warning("ollama model %s failed: %s", model, exc)
                continue
        logger.warning("all ollama models failed")
        return ""

    def _call_ollama(self, model: str, system_prompt: str, user_prompt: str) -> str:
        # Use /api/generate instead of /api/chat (more reliable)
        full_prompt = user_prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

        resp = httpx.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "num_predict": self.max_words * 4,
                    "temperature": 0.7,
                },
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("response", "").strip()
        return content

    def check_health(self) -> bool:
        try:
            resp = httpx.get(f"{self.ollama_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:  # noqa: BLE001
            return False


class TemplateNarrator(BaseNarrator):
    """Lightweight fallback that produces a short template-based summary."""

    def __init__(self, max_words: int = 80):
        super().__init__("template")
        self.max_words = max_words

    def generate(self, text: str, system_prompt: str = "", language: str = "", session_id: str = "") -> str:
        if not text.strip():
            return ""
        cleaned = _clean_for_tts(text)
        words = cleaned.split()
        if len(words) > self.max_words:
            words = words[: self.max_words]
        return "Kurze Zusammenfassung: " + " ".join(words)

    def check_health(self) -> bool:
        return True


class PassthroughNarrator(BaseNarrator):
    """Offline fallback: returns the filtered text (trimmed) as narration."""

    def __init__(self, max_words: int = 80):
        super().__init__("passthrough")
        self.max_words = max_words

    def generate(self, text: str, system_prompt: str = "", language: str = "", session_id: str = "") -> str:
        if not text.strip():
            return ""
        words = text.strip().split()
        if len(words) > self.max_words:
            words = words[: self.max_words]
        return " ".join(words)

    def check_health(self) -> bool:
        return True
