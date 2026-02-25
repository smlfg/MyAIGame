#!/usr/bin/env python3
"""Claude Code Stop hook — sends final response to MultiKanalAgent daemon.

Receives the Stop event JSON on stdin. Reads the transcript file
to extract the last assistant text, and POSTs it for narration.

IRON RULE: Always exit 0. Never block the agent.
"""

import json
import os
import sys


def _read_last_assistant_text(transcript_path: str, max_lines: int = 50) -> str:
    """Read the transcript JSONL and extract the last assistant text."""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return ""

    # Walk backwards to find the last assistant message
    for line in reversed(lines[-max_lines:]):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Look for assistant message with text content
        if entry.get("role") == "assistant":
            content = entry.get("content", [])
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                if texts:
                    return "\n".join(texts)

        # Also check for message wrapper format
        msg = entry.get("message", {})
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            content = msg.get("content", [])
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                if texts:
                    return "\n".join(texts)

    return ""


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)

        # Don't narrate if a stop hook is already active (prevent loops)
        if data.get("stop_hook_active"):
            sys.exit(0)

        # Read the transcript to get the last assistant message
        transcript_path = data.get("transcript_path", "")
        if not transcript_path:
            sys.exit(0)

        session_id = os.path.basename(transcript_path).replace(".jsonl", "") if transcript_path else ""

        text = _read_last_assistant_text(transcript_path)
        if not text or not text.strip():
            sys.exit(0)

        # Truncate to reasonable size for narration
        text = text[:3000]

        # Send to daemon (fire-and-forget: don't wait for narration to finish)
        import http.client

        payload = json.dumps({"text": text, "source": "claude_stop", "session_id": session_id}).encode()

        try:
            conn = http.client.HTTPConnection("127.0.0.1", 7742, timeout=2)
            conn.request("POST", "/narrate", body=payload,
                         headers={"Content-Type": "application/json"})
            conn.close()
        except Exception:
            pass  # Daemon might not be running — that's fine

    except Exception:
        pass  # Iron Rule: never fail

    sys.exit(0)


if __name__ == "__main__":
    main()
