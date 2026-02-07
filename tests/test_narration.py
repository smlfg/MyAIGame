"""Tests for narration generator and prompt loader."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from multikanal.narration.prompt import PromptWatcher
from multikanal.narration.generator import NarrationGenerator
from multikanal.narration.providers import BaseNarrator


def test_prompt_watcher_loads_file():
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    f.write("You are a helpful narrator.")
    f.close()

    watcher = PromptWatcher(f.name)
    assert watcher.get_prompt() == "You are a helpful narrator."
    os.unlink(f.name)


def test_prompt_watcher_missing_file():
    watcher = PromptWatcher("/nonexistent/path/prompt.md")
    assert watcher.get_prompt() == ""


def test_prompt_watcher_empty_path():
    watcher = PromptWatcher("")
    assert watcher.get_prompt() == ""


def test_prompt_watcher_thread_safe():
    """get_prompt should be callable from multiple threads."""
    import threading

    f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
    f.write("test prompt")
    f.close()

    watcher = PromptWatcher(f.name)
    results = []

    def read_prompt():
        results.append(watcher.get_prompt())

    threads = [threading.Thread(target=read_prompt) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(r == "test prompt" for r in results)
    os.unlink(f.name)


class _DummyProvider(BaseNarrator):
    def __init__(self, name: str, result: str = "", ok: bool = True):
        super().__init__(name)
        self.result = result
        self.ok = ok
        self.calls = 0

    def generate(self, text: str, system_prompt: str = "", language: str = "") -> str:
        self.calls += 1
        return self.result

    def check_health(self) -> bool:
        return self.ok


def test_generator_uses_first_successful_provider():
    p1 = _DummyProvider("p1", result="")
    p2 = _DummyProvider("p2", result="hello")
    gen = NarrationGenerator([p1, p2])
    out = gen.generate("text")
    assert out == "hello"
    assert p1.calls == 1 and p2.calls == 1


def test_generator_health_map():
    p1 = _DummyProvider("p1", ok=True)
    p2 = _DummyProvider("p2", ok=False)
    gen = NarrationGenerator([p1, p2])
    status = gen.health_map()
    assert status["p1"] is True
    assert status["p2"] is False


def test_generator_skips_empty_providers():
    """Empty results should cascade to the next provider."""
    p1 = _DummyProvider("minimax", result="")
    p2 = _DummyProvider("ollama", result="")
    p3 = _DummyProvider("template", result="fallback text")
    gen = NarrationGenerator([p1, p2, p3])
    out = gen.generate("input")
    assert out == "fallback text"
    assert p1.calls == 1
    assert p2.calls == 1
    assert p3.calls == 1


def test_minimax_provider_config():
    """MinimaxNarrator should accept correct endpoint and model."""
    from multikanal.narration.providers import MinimaxNarrator

    mm = MinimaxNarrator(
        api_key="test-key",
        endpoint="https://api.minimax.io/v1/chat/completions",
        model="MiniMax-M2.1",
    )
    assert mm.name == "minimax"
    assert mm.model == "MiniMax-M2.1"
    assert "api.minimax.io" in mm.endpoint
