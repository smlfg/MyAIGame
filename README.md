# MyAIGame – MultiKanalAgent TTS

Dual-channel CLI assistant: your coding agents work normally in the terminal while a sidecar daemon narrates what's happening through audio. This branch (`feature/tts`) brings the multikanal TTS stack into the MyAIGame repo.

## Architecture

Unlike prompt-based approaches, MultiKanalAgent uses a **daemon architecture** that never modifies the agent's prompt:

```
Agent (Claude Code / Codex / OpenCode)
  │  hooks / events / JSON output
  ▼
Adapter → POST /narrate → Daemon (FastAPI :7742)
                            ├── Filter (strip code, paths, noise)
                            ├── Narrate (provider chain: Minimax → Ollama fallback)
                            ├── Synthesize (Piper TTS)
                            └── Play (async audio)
```

## Quick Start

```bash
# Install everything
bash scripts/install.sh

# Activate environment
source .venv/bin/activate

# Start the daemon
multikanal daemon

# Test it
multikanal narrate "I just fixed a bug in the authentication module"

# Check status
multikanal health

# Install Claude Code hooks
multikanal install-hooks
```

## Requirements

- **Python 3.11+**
- **Ollama** with a model (llama3.1:8b recommended) for fallback: https://ollama.ai
- **Piper TTS** (auto-installed by `install-piper.sh`)
- **Audio playback**: paplay, aplay, or ffplay (usually pre-installed)
- **Minimax API key** (optional but preferred for primary narrator) via `MINIMAX_API_KEY`

## Configuration

Edit `config/default.yaml` or create a custom config:

```bash
MULTIKANAL_CONFIG=~/.config/multikanal.yaml multikanal daemon
```

Key narration settings:
- `narration.providers`: ordered list; default is Minimax primary (uses `MINIMAX_API_KEY`) then Ollama fallback.
- `narration.language_hint`: `auto|de|en` passed to voice selection.
- Narration prompt (`config/audio_prompt.md`) is hot-reloadable — edit while the daemon runs.

## Adapters

| Agent | How It Works |
|-------|-------------|
| **Claude Code** | Hooks (Stop + PostToolUse) send output to daemon |
| **Codex** | Wrapper runs `codex exec --json` and captures JSONL events |
| **OpenCode** | SSE subscriber listens to event stream |

## The Iron Rule

> The visual channel must NEVER be affected by audio failures.

If Ollama is down, Piper crashes, or the daemon isn't running — the agent keeps working exactly as before. Audio is purely additive.

## Testing

```bash
pytest tests/ -v
bash scripts/test-voice.sh
```
