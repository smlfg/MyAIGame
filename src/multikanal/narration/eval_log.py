"""Evaluation logger for narration quality metrics.

Writes one JSONL line per narration with quality heuristics
for systematic prompt tuning.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("multikanal.narration.eval_log")

# German stopwords (common filler/function words)
_DE_STOPWORDS = frozenset(
    "der die das ein eine einer eines einem einen und oder aber auch"
    " ist sind war waren wird werden hat haben hatte hatten kann können"
    " muss müssen soll sollen darf dürfen mag mögen will wollen"
    " ich du er sie es wir ihr man sich mich dich uns euch"
    " in an auf aus bei mit von zu für um über nach durch"
    " als wie wenn dass ob weil da so nicht noch schon sehr"
    " ja nein nur bereits also doch dort hier nun dann dort"
    " im am zum zur vom beim ins ans des dem den".split()
)

# Filler phrases banned by the prompt
_FILLER_PHRASES = [
    "es wurde",
    "das bedeutet",
    "zusammenfassend",
    "grundsätzlich",
    "im grunde",
    "man kann sagen",
]


def _prompt_hash(prompt: str) -> str:
    """SHA256 first 8 hex chars of the system prompt."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]


def _count_words(text: str) -> int:
    return len(text.split())


def _info_density(text: str) -> float:
    """Ratio of content words to total words (higher = denser)."""
    words = text.lower().split()
    if not words:
        return 0.0
    content = [w for w in words if w.strip(".,;:!?—–-\"'()") not in _DE_STOPWORDS]
    return round(len(content) / len(words), 2)


def _filler_count(text: str) -> int:
    """Count how many banned filler phrases appear."""
    lower = text.lower()
    return sum(1 for phrase in _FILLER_PHRASES if phrase in lower)


def _starts_with_filler(text: str) -> bool:
    """Does the narration open with a banned filler phrase?"""
    lower = text.lower().strip()
    return any(lower.startswith(phrase) for phrase in _FILLER_PHRASES)


class EvalLogger:
    """Appends one JSONL line per narration with quality heuristics."""

    def __init__(self, log_path: str | Path):
        self._path = Path(log_path).expanduser()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("eval logger → %s", self._path)

    def log_sample(
        self,
        *,
        source: str,
        provider: str,
        system_prompt: str,
        input_text: str,
        narration: str,
        llm_ms: int,
    ) -> None:
        """Log a single narration sample with computed metrics."""
        in_chars = len(input_text)
        out_chars = len(narration)
        out_words = _count_words(narration)

        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": source,
            "provider": provider,
            "in_chars": in_chars,
            "out_chars": out_chars,
            "out_words": out_words,
            "prompt_hash": _prompt_hash(system_prompt),
            "llm_ms": llm_ms,
            "filler_count": _filler_count(narration),
            "starts_filler": _starts_with_filler(narration),
            "info_density": _info_density(narration),
            "compression": round(in_chars / out_chars, 2) if out_chars else 0.0,
            "input_preview": input_text[:80],
            "narration": narration,
        }

        try:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning("eval log write failed: %s", exc)
