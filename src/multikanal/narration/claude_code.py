"""Claude Code narrator for narration generation."""

from __future__ import annotations

import subprocess
import json
import logging
from typing import Optional

from .providers import BaseNarrator

logger = logging.getLogger("multikanal.narration.providers")


class ClaudeCodeNarrator(BaseNarrator):
    """Generate narration using Claude Code CLI."""

    def __init__(
        self,
        claude_path: str = "/home/smlflg/.local/bin/claude",
        max_words: int = 80,
        timeout: int = 30,
    ):
        super().__init__("claude_code")
        self.claude_path = claude_path
        self.max_words = max_words
        self.timeout = timeout

    def generate(self, text: str, system_prompt: str = "", language: str = "") -> str:
        if not text.strip():
            return ""

        prompt = f"""{system_prompt}

Agent-Ausgabe:
{text}

Erstelle eine AUDIO-Erklärung (maximal {self.max_words} Wörter).
- Fokus: warum / Bedeutung / Kontext
- Kein Code, keine Dateipfade
- Ton: freundlicher Lehrer
- Antwort: nur die Erklärung, keine Einleitung"""

        try:
            result = subprocess.run(
                [
                    self.claude_path,
                    "-p",
                    "--output-format",
                    "text",
                    prompt,
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode == 0:
                narration = result.stdout.strip()
                if narration:
                    logger.info(f"Claude Code narration: {len(narration)} chars")
                    return narration
            else:
                logger.warning(f"Claude Code failed: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            logger.warning("Claude Code timed out")
        except Exception as exc:
            logger.debug(f"Claude Code error: {exc}")

        return ""

    def check_health(self) -> bool:
        try:
            result = subprocess.run(
                [self.claude_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False
