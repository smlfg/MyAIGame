#!/usr/bin/env python3
"""Claude Code PostToolUse hook — syntax-check Python files after Edit/Write.

Receives PostToolUse JSON on stdin. If the edited file is .py,
runs py_compile to catch syntax errors immediately.

IRON RULE: Always exit 0. Never block the agent.
"""

import json
import subprocess
import sys


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)

        tool_input = data.get("tool_input", {})
        if not isinstance(tool_input, dict):
            sys.exit(0)

        file_path = tool_input.get("file_path", "")

        # Only check Python files
        if not file_path.endswith(".py"):
            sys.exit(0)

        result = subprocess.run(
            ["python3", "-m", "py_compile", file_path],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error_msg = (result.stderr or result.stdout).strip()[:500]
            print(f"⚠ Syntax error in {file_path}:\n{error_msg}", file=sys.stderr)

    except Exception:
        pass  # Iron Rule: never fail

    sys.exit(0)


if __name__ == "__main__":
    main()
