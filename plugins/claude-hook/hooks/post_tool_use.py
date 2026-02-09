#!/usr/bin/env python3
"""Claude Code PostToolUse hook — sends tool results to MultiKanalAgent daemon.

Receives the PostToolUse event JSON on stdin, extracts the tool
result text, and POSTs it to the daemon for narration.

IRON RULE: Always exit 0. Never block the agent.
"""

import json
import sys

# Tools that produce noise — skip narration for these
SKIP_TOOLS = {"Read", "Glob", "Grep", "WebSearch", "WebFetch"}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)

        tool_name = data.get("tool_name", "unknown")

        # Skip noisy tools
        if tool_name in SKIP_TOOLS:
            sys.exit(0)

        # Extract text from tool_response (the actual result)
        response = data.get("tool_response", {})
        text = ""
        if isinstance(response, str):
            text = response
        elif isinstance(response, dict):
            # Try common response fields
            for key in ("content", "text", "output", "stdout", "result"):
                val = response.get(key)
                if isinstance(val, str) and val.strip():
                    text = val
                    break
            # For Bash tool: stdout is the main output
            if not text and "stdout" in response:
                text = str(response["stdout"])

        # Also check tool_input for context
        tool_input = data.get("tool_input", {})
        context = ""
        if isinstance(tool_input, dict):
            # For Bash: include the command
            cmd = tool_input.get("command", "")
            desc = tool_input.get("description", "")
            if desc:
                context = desc
            elif cmd:
                context = f"Command: {cmd}"

        if not text.strip():
            sys.exit(0)

        # Build narration input with context
        if context:
            narration_input = f"{context}\n\nResult:\n{text[:2000]}"
        else:
            narration_input = f"Tool '{tool_name}' result:\n{text[:2000]}"

        # Send to daemon (fire-and-forget: don't wait for narration to finish)
        import http.client
        import urllib.parse

        payload = json.dumps({
            "text": narration_input,
            "source": "claude_code",
        }).encode()

        try:
            conn = http.client.HTTPConnection("127.0.0.1", 7742, timeout=2)
            conn.request("POST", "/narrate", body=payload,
                         headers={"Content-Type": "application/json"})
            # Don't wait for response — daemon handles narration async
            conn.close()
        except Exception:
            pass  # Daemon might not be running

    except Exception:
        pass  # Iron Rule: never fail

    sys.exit(0)


if __name__ == "__main__":
    main()
