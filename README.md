# AI Command Explainer

Linux-Befehle verständlich erklärt — mit Sprachausgabe.

```bash
ai grep          # Was macht grep?
ai chmod -R      # Was macht chmod -R?
ai systemctl     # Was macht systemctl?
```

## Was passiert

1. `ai` holt die man-page des Befehls
2. Schickt sie an **MiniMax M2.1** (online, ~3s) oder **Ollama/codellama** (lokal, Fallback)
3. Zeigt die Erklärung im Terminal
4. Liest sie über den **MultiKanal TTS Daemon** vor (wenn er läuft)

## Installation

```bash
# Scripts nach ~/bin kopieren
cp bin/ai ~/bin/ai
cp bin/ai-speak ~/bin/ai-speak
chmod +x ~/bin/ai ~/bin/ai-speak

# MiniMax API Key (optional, aber empfohlen — viel schneller als Ollama)
echo 'MINIMAX_API_KEY=dein-key-hier' >> ~/.env

# Ollama als Fallback (lokal)
ollama pull codellama
```

## TTS Sprachausgabe

Wenn der MultiKanal TTS Daemon auf Port 7742 läuft, wird die Erklärung automatisch vorgelesen.
Ohne Daemon wird `ai-speak` als Fallback genutzt (Edge TTS → Piper → spd-say).

Siehe Branch `SpeakignAgents` für den TTS Daemon.

## Abhängigkeiten

- `python3` (für MiniMax API Calls und TTS)
- `curl` (für Health-Checks)
- `ollama` + `codellama` (Fallback, optional wenn MiniMax Key vorhanden)
- `edge-tts` (für `ai-speak` Fallback): `pip install edge-tts`
