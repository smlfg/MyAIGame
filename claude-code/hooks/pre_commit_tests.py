#!/usr/bin/env python3
"""Claude Code PreToolUse hook — run tests before git commit.

Receives PreToolUse JSON on stdin. If the Bash command is a git commit,
runs pytest first. Blocks the commit if tests fail.

Only triggers on actual 'git commit' commands, not mentions in strings.
"""

import json
import os
import re
import subprocess
import sys


def is_git_commit_command(command: str) -> bool:
    """Check if the command is actually running git commit (not just mentioning it)."""
    # Strip leading whitespace and common prefixes
    cmd = command.strip()
    # Match patterns like: git commit, git add . && git commit, etc.
    # But not: echo "git commit", # git commit (comments)
    if cmd.startswith("#") or cmd.startswith("echo "):
        return False
    # Check for git commit as an actual command in a chain
    parts = re.split(r"[;&|]+", cmd)
    for part in parts:
        part = part.strip()
        if part.startswith("git commit") or part.startswith("git -c") and "commit" in part:
            return True
    return False


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)

        tool_input = data.get("tool_input", {})
        if not isinstance(tool_input, dict):
            sys.exit(0)

        command = tool_input.get("command", "")

        # Only intercept actual git commit commands
        if not is_git_commit_command(command):
            sys.exit(0)

        # Find git repository root
        toplevel = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if toplevel.returncode != 0:
            sys.exit(0)

        repo_dir = toplevel.stdout.strip()

        # Check if any test files exist
        has_tests = False
        for root, dirs, files in os.walk(repo_dir):
            # Skip hidden dirs and common non-test dirs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".venv")]
            for f in files:
                if f.startswith("test_") and f.endswith(".py") or f.endswith("_test.py"):
                    has_tests = True
                    break
            if has_tests:
                break

        if not has_tests:
            sys.exit(0)  # No tests found, allow commit

        # Walk up directory tree to find a venv Python (up to 4 levels)
        python_exe = "python3"
        search_dir = repo_dir
        for _ in range(5):
            for venv_name in (".venv", "venv"):
                candidate = os.path.join(search_dir, venv_name, "bin", "python")
                if os.path.isfile(candidate):
                    python_exe = candidate
                    break
            if python_exe != "python3":
                break
            parent = os.path.dirname(search_dir)
            if parent == search_dir:
                break
            search_dir = parent

        # Run tests
        result = subprocess.run(
            [python_exe, "-m", "pytest", "--tb=short", "-q"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=repo_dir,
        )

        # Exit code 5 = no tests collected (e.g. all test dirs excluded via norecursedirs)
        if result.returncode not in (0, 5):
            output = (result.stdout + "\n" + result.stderr).strip()[-800:]
            # Output block decision as JSON so Claude sees the failure
            print(json.dumps({
                "decision": "block",
                "reason": f"Tests failed! Fix before committing:\n{output}",
            }))
            sys.exit(2)

    except Exception:
        pass  # If anything goes wrong, allow the commit

    sys.exit(0)


if __name__ == "__main__":
    main()
