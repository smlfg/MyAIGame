# Speaking Agents — MultiKanal TTS Daemon

Gibt deinen Coding-Agents eine Stimme. Florian (Claude Code), Seraphina (Codex), Conrad (OpenCode), Killian (Gemini).

## So funktioniert's

Ein FastAPI-Daemon läuft im Hintergrund auf `localhost:7742`. Jedes Tool das Sprache will, schickt einen HTTP-POST:

```bash
curl -X POST http://localhost:7742/narrate \
  -H 'Content-Type: application/json' \
  -d '{"text": "Ich habe die Datei geändert.", "source": "claude_code"}'
```

Der Daemon:
1. Fasst den Text mit **MiniMax M2.1** zusammen (oder Ollama als Fallback)
2. Synthetisiert Audio mit **Edge TTS** (Microsoft Neural Voices)
3. Spielt es ab mit **paplay/ffplay**

Für bereits fertigen Text (z.B. von `ai`-Skript) gibt es `direct_tts: true` — überspringt den LLM-Schritt.

## Installation

```bash
# 1. Repo klonen
git clone -b SpeakignAgents https://github.com/smlfg/MyAIGame.git multikanal-tts
cd multikanal-tts

# 2. Venv + Dependencies
python3 -m venv .venv
.venv/bin/pip install -e .

# 3. MiniMax API Key
cp .env.example .env
# Editiere .env und trage deinen Key ein

# 4. Daemon starten
.venv/bin/multikanal daemon
```

## Autostart (systemd)

```bash
cp systemd/multikanal.service ~/.config/systemd/user/
# Editiere den Service: Pfade anpassen!
systemctl --user daemon-reload
systemctl --user enable --now multikanal.service
```

## Claude Code Hooks

Damit Florian bei jedem Tool-Aufruf spricht, füge in `~/.claude/settings.json` hinzu:

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python3 /pfad/zu/plugins/claude-hook/hooks/stop.py",
        "timeout": 10, "async": true
      }]
    }],
    "PostToolUse": [{
      "matcher": "Bash|Edit|Write|Task",
      "hooks": [{
        "type": "command",
        "command": "python3 /pfad/zu/plugins/claude-hook/hooks/post_tool_use.py",
        "timeout": 10, "async": true
      }]
    }]
  }
}
```

## Stimmen

| Agent | Stimme | Edge TTS Voice |
|-------|--------|----------------|
| Claude Code | Florian | de-DE-FlorianMultilingualNeural |
| Codex | Seraphina | de-DE-SeraphinaMultilingualNeural |
| OpenCode | Conrad | de-DE-ConradNeural |
| Gemini | Killian | de-DE-KillianNeural |

## API

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/narrate` | POST | Text narieren + vorlesen |
| `/health` | GET | Status aller Provider |
| `/stop` | POST | Audio stoppen |

### POST /narrate

```json
{
  "text": "Agent output hier...",
  "source": "claude_code",
  "direct_tts": false
}
```

- `source`: bestimmt Stimme und Prefix
- `direct_tts: true`: überspringt LLM, spricht Text direkt

## Architektur

```
Claude Code Hook ──┐
ai-Skript ─────────┤
Codex Wrapper ─────┤──► Daemon :7742 ──► MiniMax/Ollama ──► Edge TTS ──► paplay
OpenCode SSE ──────┘         │
                        asyncio.Lock (Mutex: kein Überlappen)
                        asyncio.Queue (Audio-Queue: nacheinander)
```
