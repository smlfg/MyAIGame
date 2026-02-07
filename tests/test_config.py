"""Tests for configuration loading."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from multikanal.config import _deep_merge, load_config


def test_deep_merge_basic():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99}, "e": 5}
    result = _deep_merge(base, override)
    assert result["a"] == 1
    assert result["b"]["c"] == 99
    assert result["b"]["d"] == 3
    assert result["e"] == 5


def test_deep_merge_does_not_mutate():
    base = {"a": {"b": 1}}
    override = {"a": {"b": 2}}
    result = _deep_merge(base, override)
    assert base["a"]["b"] == 1
    assert result["a"]["b"] == 2


def test_load_default_config():
    cfg = load_config()
    assert "daemon" in cfg
    assert cfg["daemon"]["port"] == 7742
    assert cfg["daemon"]["host"] == "127.0.0.1"
    assert "narration" in cfg
    assert "tts" in cfg
    assert "cache" in cfg


def test_load_custom_config():
    custom = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    )
    custom.write("daemon:\n  port: 9999\n")
    custom.close()

    cfg = load_config(custom.name)
    assert cfg["daemon"]["port"] == 9999
    # Other defaults still present
    assert cfg["daemon"]["host"] == "127.0.0.1"
    os.unlink(custom.name)


def test_path_expansion():
    cfg = load_config()
    cache_path = cfg["cache"]["path"]
    assert "~" not in cache_path


def test_env_var_port_override(monkeypatch):
    monkeypatch.setenv("MULTIKANAL_PORT", "8888")
    cfg = load_config()
    assert cfg["daemon"]["port"] == 8888


def test_narration_models_list():
    cfg = load_config()
    providers = cfg["narration"].get("providers", [])
    assert isinstance(providers, list)
    assert len(providers) >= 1
    names = [p.get("name") for p in providers if isinstance(p, dict)]
    assert "minimax" in names or "ollama" in names


def test_minimax_is_first_provider():
    """MiniMax should be the primary (first) narration provider."""
    cfg = load_config()
    providers = cfg["narration"]["providers"]
    assert len(providers) >= 2
    assert providers[0]["name"] == "minimax"
    assert providers[0]["enabled"] is True


def test_minimax_provider_defaults():
    """MiniMax provider should have correct endpoint and model."""
    cfg = load_config()
    providers = cfg["narration"]["providers"]
    mm = next(p for p in providers if p["name"] == "minimax")
    assert "api.minimax.io" in mm["endpoint"]
    assert mm["model"] == "MiniMax-M2.1"
    assert 0 < mm["temperature"] <= 1.0


def test_provider_chain_order():
    """Provider chain should be: minimax, ollama, template, passthrough."""
    cfg = load_config()
    providers = cfg["narration"]["providers"]
    names = [p["name"] for p in providers]
    assert names.index("minimax") < names.index("ollama")
    # template and passthrough should come after ollama
    assert names.index("ollama") < names.index("template")
    assert names.index("template") < names.index("passthrough")
