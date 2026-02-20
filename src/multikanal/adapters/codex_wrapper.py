"""Codex CLI wrapper adapter with live JSONL streaming.

Wraps `codex exec --json "prompt"` and reads JSONL events in real-time.
Each agent_message event is sent to the daemon immediately (live narration).
At turn.completed, an accumulated summary is sent (final narration).

Two modes of operation:
  - Live: `run_live(prompt)` — starts codex, streams events to daemon
  - One-shot: `capture(prompt=...)` — runs codex, returns accumulated text
"""

import json
import logging
import subprocess
import sys

from .base import BaseAdapter

logger = logging.getLogger("multikanal.adapters.codex_wrapper")


class CodexWrapperAdapter(BaseAdapter):
    """Wraps Codex CLI in JSON mode with live narration support."""

    def __init__(
        self,
        daemon_url: str = "http://127.0.0.1:7742",
        codex_command: str = "codex",
    ):
        super().__init__(daemon_url)
        self._command = codex_command

    def capture(self, **kwargs) -> str:
        """Run codex and return accumulated text (one-shot, blocking)."""
        prompt = kwargs.get("prompt", "")
        if not prompt:
            return ""

        texts = []
        for _event_type, text in self._stream_events(prompt):
            if text:
                texts.append(text)
        return "\n".join(texts)

    def run_live(self, prompt: str) -> str:
        """Run codex with live narration — sends events to daemon in real-time.

        Each agent_message is narrated immediately with source="codex".
        At turn.completed, accumulated text is narrated with source="codex_final".

        Returns the full accumulated output text.
        """
        accumulated: list[str] = []

        for event_type, text in self._stream_events(prompt):
            if not text:
                continue

            # Always print to terminal (visual channel)
            print(text)

            if event_type == "agent_message":
                accumulated.append(text)
                # Live: narrate immediately
                self.send_to_daemon(text, source="codex", timeout=30)

            elif event_type == "reasoning":
                # Don't narrate reasoning, but accumulate for summary
                accumulated.append(f"(Reasoning: {text})")

            elif event_type == "turn_completed":
                # Final summary
                if accumulated:
                    summary = "\n".join(accumulated)
                    self.send_to_daemon(summary, source="codex_final", timeout=60)

        return "\n".join(accumulated)

    def _stream_events(self, prompt: str):
        """Generator: yields (event_type, text) tuples from codex JSONL stream.

        Event types:
          - "agent_message": assistant text response
          - "reasoning": model reasoning/thinking
          - "tool_call": tool execution
          - "turn_completed": codex finished
        """
        cmd = [self._command, "exec", "--json", prompt]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError:
            logger.warning("codex command not found: %s", self._command)
            return

        try:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    yield ("raw", line)
                    continue

                event_type = event.get("type", "")
                item = event.get("item", {})

                if event_type == "item.completed":
                    item_type = item.get("type", "")
                    text = item.get("text", "")

                    if item_type == "agent_message" and text:
                        yield ("agent_message", text)
                    elif item_type == "reasoning" and text:
                        yield ("reasoning", text)
                    elif item_type == "tool_call":
                        # Tool calls: extract command/function name
                        name = item.get("name", item.get("function", ""))
                        args = item.get("arguments", "")
                        if name:
                            yield ("tool_call", f"Tool: {name}")

                elif event_type == "turn.completed":
                    yield ("turn_completed", "")

            proc.wait(timeout=300)

        except subprocess.TimeoutExpired:
            proc.kill()
            logger.warning("codex timed out after 300s")
        except Exception as e:
            logger.warning("error reading codex output: %s", e)

    def run_and_narrate(self, prompt: str) -> tuple[str, dict | None]:
        """Legacy: run codex one-shot, narrate at end.

        For live narration, use run_live() instead.
        """
        text = self.capture(prompt=prompt)
        if text:
            print(text)
        response = self.send_to_daemon(text, source="codex")
        return text, response
