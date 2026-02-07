"""YAML configuration loader with deep merge and env var overrides."""

import os
import pathlib
from typing import Any

import yaml


def _guess_project_root() -> pathlib.Path:
    """Find project root by walking up for config/default.yaml; fallback to CWD."""
    here = pathlib.Path(__file__).resolve()
    for candidate in [here] + list(here.parents):
        cfg = candidate / "config" / "default.yaml"
        if cfg.exists():
            return candidate
    return pathlib.Path.cwd()


PROJECT_ROOT = _guess_project_root()


def _load_dotenv():
    """Load environment variables from .env file."""
    env_paths = [
        pathlib.Path.cwd() / ".env",
        PROJECT_ROOT / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            try:
                from dotenv import load_dotenv

                load_dotenv(env_path, override=True)
                break
            except ImportError:
                # python-dotenv not installed, try manual parsing
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, val = line.split("=", 1)
                            os.environ[key.strip()] = val.strip()


_load_dotenv()


DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.yaml"

DEFAULT_CONFIG: dict[str, Any] = {
    "daemon": {
        "host": "127.0.0.1",
        "port": 7742,
        "log_level": "info",
    },
    "adapters": {
        "default": "claude_hook",
    },
    "narration": {
        # Provider chain (preferred)
        "providers": [
            {
                "name": "minimax",
                "enabled": True,
                "endpoint": "https://api.minimax.io/v1/chat/completions",
                "model": "MiniMax-M2.1",
                "temperature": 0.6,
                "max_tokens": 600,
                "timeout_seconds": 8,
            },
            {
                "name": "ollama",
                "enabled": True,
                "ollama_url": "http://localhost:11434",
                "models": ["llama3.1:8b", "phi4", "mistral-nemo"],
                "timeout_seconds": 10,
            },
        ],
        # Legacy fields (used if providers not set)
        "models": ["llama3.1:8b", "phi4", "mistral-nemo"],
        "ollama_url": "http://localhost:11434",
        "max_input_chars": 2000,
        "max_output_words": 200,
        "timeout_seconds": 10,
        "prompt_file": "config/audio_prompt.md",
        "language_hint": "auto",
    },
    "tts": {
        "engine": "piper",
        "command": "",
        "voices": {"de": "de_DE-thorsten-medium", "en": "en_US-lessac-medium"},
        "default_voice": "de",
        "speed": 1.0,
        "sentence_streaming": True,
    },
    "playback": {
        "tool": "",
        "volume": 1.0,
    },
    "cache": {
        "path": "~/.cache/multikanal",
        "max_entries": 500,
    },
    "logging": {
        "path": "~/.local/share/multikanal/logs",
        "level": "info",
        "json": True,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base, returning a new dict."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _expand_path(path_str: str) -> str:
    """Expand ~ and environment variables in a path string."""
    return str(pathlib.Path(os.path.expandvars(os.path.expanduser(path_str))))


def _resolve_prompt_path(prompt_file: str) -> str:
    """Resolve prompt file path relative to project root."""
    p = pathlib.Path(prompt_file)
    if p.is_absolute():
        return str(p)

    # Try project root first
    prj_path = (PROJECT_ROOT / prompt_file).resolve()
    if prj_path.exists():
        return str(prj_path)

    # Fallback: current working directory
    cwd_path = (pathlib.Path.cwd() / prompt_file).resolve()
    return str(cwd_path)


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load configuration with precedence: file > env > defaults."""
    env_path = os.environ.get("MULTIKANAL_CONFIG")
    path = config_path or env_path

    cfg: dict[str, Any] = dict(DEFAULT_CONFIG)

    yaml_path: pathlib.Path | None = None
    if path:
        yaml_path = pathlib.Path(os.path.expanduser(path))
        if not yaml_path.is_absolute():
            yaml_path = (PROJECT_ROOT / yaml_path).resolve()
    else:
        yaml_path = DEFAULT_CONFIG_PATH

    if yaml_path and yaml_path.exists():
        with open(yaml_path, encoding="utf-8") as f:
            file_cfg = yaml.safe_load(f) or {}
        cfg = _deep_merge(cfg, file_cfg)

    # Expand paths
    for section, key in [("cache", "path"), ("logging", "path")]:
        val = cfg.get(section, {}).get(key)
        if val:
            cfg[section][key] = _expand_path(val)

    # Resolve prompt file path
    prompt_file = cfg.get("narration", {}).get("prompt_file")
    if prompt_file:
        cfg["narration"]["prompt_file"] = _resolve_prompt_path(prompt_file)

    # Inject env-based secrets (Minimax API key)
    providers = cfg.get("narration", {}).get("providers", [])
    api_key = os.environ.get("MINIMAX_API_KEY")
    for provider in providers:
        if isinstance(provider, dict) and provider.get("name") == "minimax":
            if api_key and not provider.get("api_key"):
                provider["api_key"] = api_key

    # Env var overrides
    env_port = os.environ.get("MULTIKANAL_PORT")
    if env_port:
        cfg["daemon"]["port"] = int(env_port)

    env_ollama = os.environ.get("OLLAMA_HOST")
    if env_ollama:
        cfg["narration"]["ollama_url"] = env_ollama

    return cfg
