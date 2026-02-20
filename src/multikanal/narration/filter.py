"""Filter agent output to extract meaningful text for narration.

Strips code fences, file paths, tool call JSON, and other noise that
would confuse the narration LLM or produce bad TTS output.
"""

import re

# Code fences: ```...```
_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)

# Inline code: `...`
_INLINE_CODE_RE = re.compile(r"`[^`]+`")

# File paths: /foo/bar/baz.py or ~/something or ./relative
_FILE_PATH_RE = re.compile(r"(?:~|\.)?/[\w./-]+")

# Tool call JSON blocks: {"tool": ..., "input": ...}
_TOOL_JSON_RE = re.compile(r'\{\s*"(?:tool|type|name|input)"[^}]*\}', re.DOTALL)

# ANSI escape codes
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Diff headers: --- a/file, +++ b/file, @@ ... @@
_DIFF_HEADER_RE = re.compile(r"^(?:---|\+\+\+|@@).*$", re.MULTILINE)

# Diff lines: lines starting with + or - (but not --- or +++)
_DIFF_LINE_RE = re.compile(r"^[+-](?![-+]{2}).*$", re.MULTILINE)

# Multiple blank lines -> single blank line
_MULTI_BLANK_RE = re.compile(r"\n{3,}")

# URLs
_URL_RE = re.compile(r"https?://\S+")


def filter_output(text: str, max_chars: int = 2000) -> str:
    """Clean agent output for narration input.

    Returns a condensed text suitable for sending to the narration LLM.
    """
    if not text:
        return ""

    result = text

    # Strip ANSI escape codes first
    result = _ANSI_RE.sub("", result)

    # Remove code fences (keep surrounding context)
    result = _CODE_FENCE_RE.sub(" [code block removed] ", result)

    # Remove inline code
    result = _INLINE_CODE_RE.sub("", result)

    # Remove tool call JSON
    result = _TOOL_JSON_RE.sub("", result)

    # Remove diff artifacts
    result = _DIFF_HEADER_RE.sub("", result)
    result = _DIFF_LINE_RE.sub("", result)

    # Remove file paths
    result = _FILE_PATH_RE.sub("", result)

    # Remove URLs
    result = _URL_RE.sub("", result)

    # Collapse whitespace
    result = _MULTI_BLANK_RE.sub("\n\n", result)
    result = result.strip()

    # Truncate to max_chars
    if len(result) > max_chars:
        result = result[:max_chars].rsplit(" ", 1)[0] + "..."

    return result
