# MyAIGame — CLAUDE.md

**Project:** multikanal — dual-channel CLI assistant (visual terminal + audio TTS narration)
**Stack:** Python 3.11+, FastAPI, hatch, pytest, ruff

---

## Build & Test

```bash
# Install (editable + dev deps)
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Build wheel
hatch build

# Run daemon
multikanal start         # or: python -m multikanal
```

**Entry point:** `src/multikanal/cli.py:main` → registered as `multikanal` script via pyproject.toml

---

## Architecture

```
multikanal/
├── daemon.py       # FastAPI app, HTTP server, lifecycle
├── cli.py          # Click/argparse CLI entry point
├── config.py       # Pydantic config, loads config/default.yaml
├── adapters/       # Output adapters (Audio, File, Console)
├── narration/      # AI-driven narration pipeline
└── tts/            # TTS engines (Edge TTS → Piper → spd-say fallback)
```

**Two channels:**
1. **Visual** — Terminal output, formatted text
2. **Audio** — TTS narration via Edge TTS (primary), Piper (fallback), spd-say (last resort)

**Plugin system:** `plugins/claude-hook/` — hook scripts that inject context into Claude Code.

---

## Key Files

| File | Purpose |
|------|---------|
| `src/multikanal/daemon.py` | FastAPI daemon — main server process |
| `src/multikanal/cli.py` | CLI entry point (`multikanal` command) |
| `src/multikanal/config.py` | Config loading from `config/default.yaml` |
| `config/default.yaml` | Runtime configuration |
| `plugins/claude-hook/hooks/` | Claude Code hook scripts |
| `systemd/multikanal.service` | Systemd service definition |
| `pyproject.toml` | Build system config (hatch) |

**Companion tools:**
- `bin/ai` — Linux command explainer (MiniMax/Ollama)
- `bin/ai-speak` — Like `ai` but with TTS output
- `session-browser/` — Streamlit GUI for Claude Code session history

---

## Rules

### Before Delegating
- Run `~/.claude/hooks/gather-context.sh` to collect project context
- Never delegate without reading the relevant source files first

### Git
- Never commit directly to `main`
- Run tests before every commit: `pytest`
- Use descriptive commit messages — "what AND why"

### Plugin Hooks
- Hooks MUST exit `0` (success) or `2` (block with message)
- JSON on stdout = `additionalContext` injection for Claude
- stderr = logging only (not shown to user)
- Always timeout-safe — graceful degradation over hard failure

### TTS Pipeline
- Edge TTS is primary — always test with audio disabled first
- Fallback chain: Edge TTS → Piper → spd-say
- Never assume audio is available — check `multikanal status` first

### Build System
- Use `hatch` for building, not setuptools directly
- Dependencies go in `pyproject.toml`, not `requirements.txt`
- Dev deps: `pytest>=8.0`, `pytest-asyncio>=0.24`

---

## Dependencies (from pyproject.toml)

```
fastapi>=0.115       # HTTP framework for daemon
uvicorn[standard]>=0.32  # ASGI server
httpx>=0.27          # Async HTTP client
pyyaml>=6.0          # Config parsing
watchdog>=5.0        # File system monitoring
```

---

## Delegation Architecture (inherited from global CLAUDE.md)

| Layer | Cost/1M | Tool | When |
|-------|---------|------|------|
| CLI | $0 | Shell scripts | Lint, test, git, find |
| Strategy | ~$15 | Claude Code | Planning, orchestration |
| Execution | ~$3 | OpenCode MCP | Code generation, refactoring |
| Research | ~$0.10 | Gemini MCP | Web research, fact-checking |

**Gemini FIRST for research. OpenCode for implementation. Never implement without a plan.**

---

## Common Tasks

```bash
# Check daemon status
multikanal status

# Speak something
echo "Hello World" | multikanal speak

# Run with custom config
multikanal --config config/custom.yaml start

# View session browser
cd session-browser && ./run.sh
```
