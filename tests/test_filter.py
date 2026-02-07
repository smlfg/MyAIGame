"""Tests for narration output filter."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from multikanal.narration.filter import filter_output


def test_strips_code_fences():
    text = "Here's the fix:\n```python\ndef foo():\n    return 42\n```\nThis should work."
    result = filter_output(text)
    assert "def foo" not in result
    assert "should work" in result


def test_strips_file_paths():
    text = "I edited /home/user/project/src/main.py to fix the bug."
    result = filter_output(text)
    assert "/home/user" not in result
    assert "fix the bug" in result


def test_strips_tool_json():
    text = 'Running tool: {"tool": "bash", "input": "ls -la"}\nDone.'
    result = filter_output(text)
    assert '"tool"' not in result
    assert "Done" in result


def test_strips_ansi_codes():
    text = "\x1b[32mSuccess\x1b[0m: all tests passed"
    result = filter_output(text)
    assert "\x1b[" not in result
    assert "Success" in result


def test_strips_diff_headers():
    text = "Changes:\n--- a/old.py\n+++ b/new.py\n@@ -1,3 +1,4 @@\nSome context."
    result = filter_output(text)
    assert "---" not in result
    assert "+++" not in result
    assert "@@" not in result


def test_strips_urls():
    text = "See https://docs.example.com/api for details."
    result = filter_output(text)
    assert "https://" not in result
    assert "details" in result


def test_truncates_long_input():
    text = "word " * 1000  # 5000 chars
    result = filter_output(text, max_chars=100)
    assert len(result) <= 104  # 100 + "..."


def test_empty_input():
    assert filter_output("") == ""
    assert filter_output("   ") == ""


def test_preserves_natural_language():
    text = "I added a new function to handle user authentication. It checks the JWT token and validates permissions."
    result = filter_output(text)
    assert "authentication" in result
    assert "JWT token" in result


def test_strips_inline_code():
    text = "Changed `config.yaml` to use the new `port` setting."
    result = filter_output(text)
    assert "`" not in result
