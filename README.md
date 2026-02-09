# MyAIGame — AI Skills & Tools

Wiederverwendbare AI-Skills: Sprechende Agents, Command Explainer, und mehr.

## Schnellstart (komplett, von Null)

### Voraussetzungen

- **Linux** (getestet auf Pop!_OS / Ubuntu)
- **Python 3.11+**
- **Audio**: PulseAudio mit `paplay` (auf den meisten Linux-Desktops vorinstalliert)
- **Internet**: Für MiniMax API und Edge TTS

### 1. Repo klonen

```bash
git clone https://github.com/smlfg/MyAIGame.git
cd MyAIGame
```

### 2. TTS Daemon installieren

```bash
# Venv erstellen und Dependencies installieren
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install edge-tts

# MiniMax API Key eintragen (kostenlos auf minimax.io)
cp .env.example .env
nano .env   # MINIMAX_API_KEY=dein-echter-key
```

### 3. Daemon starten

```bash
.venv/bin/multikanal daemon
```

Testen ob er läuft:
```bash
curl http://localhost:7742/health
```

### 4. ai-Command installieren (optional)

```bash
cp bin/ai ~/bin/ai
cp bin/ai-speak ~/bin/ai-speak
chmod +x ~/bin/ai ~/bin/ai-speak

# Ollama als Fallback für ai-Command (optional)
ollama pull codellama
```

### 5. Claude Code Hooks installieren (optional)

In `~/.claude/settings.json` einfügen — Pfade anpassen!

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python3 /DEIN/PFAD/ZU/MyAIGame/plugins/claude-hook/hooks/stop.py",
        "timeout": 10, "async": true
      }]
    }],
    "PostToolUse": [{
      "matcher": "Bash|Edit|Write|Task",
      "hooks": [{
        "type": "command",
        "command": "python3 /DEIN/PFAD/ZU/MyAIGame/plugins/claude-hook/hooks/post_tool_use.py",
        "timeout": 10, "async": true
      }]
    }]
  }
}
```

### 6. Autostart einrichten (optional)

```bash
cp systemd/multikanal.service ~/.config/systemd/user/
# WICHTIG: Pfade im Service anpassen!
nano ~/.config/systemd/user/multikanal.service
systemctl --user daemon-reload
systemctl --user enable --now multikanal.service
```

---

## Was ist drin?

### AI Command Explainer (`bin/ai`)

Linux-Befehle verständlich erklärt — mit Sprachausgabe.

```bash
ai grep          # Was macht grep?
ai chmod -R      # Was macht chmod -R?
ai systemctl     # Was macht systemctl?
```

Provider-Kette: MiniMax (~3s) → Ollama/codellama (Fallback, ~40s)

### MultiKanal TTS Daemon (`src/multikanal/`)

Gibt Coding-Agents eine Stimme. Jedes Tool schickt einen HTTP-POST:

```bash
curl -X POST http://localhost:7742/narrate \
  -H 'Content-Type: application/json' \
  -d '{"text": "Ich habe die Datei geändert.", "source": "claude_code"}'
```

Für fertigen Text `direct_tts: true` setzen (überspringt LLM-Zusammenfassung):

```bash
curl -X POST http://localhost:7742/narrate \
  -H 'Content-Type: application/json' \
  -d '{"text": "Fertiger Text zum Vorlesen.", "source": "ai_explain", "direct_tts": true}'
```

## Stimmen

| Agent | Stimme | Edge TTS Voice |
|-------|--------|----------------|
| Claude Code | Florian | de-DE-FlorianMultilingualNeural |
| Codex | Seraphina | de-DE-SeraphinaMultilingualNeural |
| OpenCode | Conrad | de-DE-ConradNeural |
| Gemini | Killian | de-DE-KillianNeural |
| ai-Command | Florian | de-DE-FlorianMultilingualNeural |

## API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|-------------|
| `/narrate` | POST | Text narieren + vorlesen |
| `/health` | GET | Status aller Provider |
| `/stop` | POST | Audio stoppen |

## Architektur

```
Claude Code Hook ──┐
ai-Skript ─────────┤
Codex Wrapper ─────┤──► Daemon :7742 ──► MiniMax/Ollama ──► Edge TTS ──► paplay
OpenCode SSE ──────┘         │
                        asyncio.Lock (Mutex: kein Überlappen)
                        asyncio.Queue (Audio-Queue: nacheinander)
```

## Abhängigkeiten

| Was | Wofür | Installation |
|-----|-------|-------------|
| Python 3.11+ | Alles | `apt install python3` |
| edge-tts | Sprachsynthese | `pip install edge-tts` |
| paplay | Audio abspielen | Vorinstalliert (PulseAudio) |
| curl | Health-Checks | Vorinstalliert |
| MiniMax API Key | LLM Narration | Kostenlos auf minimax.io |
| Ollama + codellama | Fallback LLM | Optional: `ollama pull codellama` |
