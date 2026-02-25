# VoiceMode Edge TTS — Latency Optimizer

Drop TTS latency from **~8s (Kokoro) to ~1.5s (Edge TTS)** by wrapping Microsoft Edge TTS as an OpenAI-compatible API server.

## What This Does

VoiceMode MCP supports any OpenAI-compatible TTS endpoint via `VOICEMODE_TTS_BASE_URLS`. This server wraps `edge-tts` (free, no API key needed) and exposes:

- `POST /v1/audio/speech` — OpenAI-compatible TTS synthesis
- `GET /v1/audio/voices` — Available voices
- `GET /v1/models` — Supported models
- `GET /health` — Server health check

## Setup

```bash
# 1. Install edge-tts
pip install edge-tts

# 2. Copy server
mkdir -p ~/.voicemode/services/edge-tts
cp server.py ~/.voicemode/services/edge-tts/

# 3. Install systemd service
cp voicemode-edge-tts.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now voicemode-edge-tts

# 4. Configure VoiceMode (add to ~/.voicemode/voicemode.env)
VOICEMODE_TTS_BASE_URLS=http://127.0.0.1:5050/v1,http://127.0.0.1:8880/v1,https://api.openai.com/v1
VOICEMODE_VOICES=florian,af_sky,alloy

# 5. Restart Claude Code so VoiceMode picks up the new config
```

## Voices

| Alias | Edge TTS Voice | Language |
|-------|---------------|----------|
| florian | de-DE-FlorianMultilingualNeural | DE |
| katja | de-DE-KatjaNeural | DE |
| conrad | de-DE-ConradNeural | DE |
| seraphina | de-DE-SeraphinaMultilingualNeural | DE |
| aria | en-US-AriaNeural | EN |
| alloy/nova/echo... | Mapped to German defaults | DE |

Direct Edge TTS voice names also work (e.g. `de-DE-KatjaNeural`).

## Latency Benchmark

| Provider | Latency | Cost |
|----------|---------|------|
| Edge TTS (this) | **~1.5s** | Free |
| Kokoro (local) | ~8s | Free |
| OpenAI API | ~3-5s | $15/1M chars |

## Bonus Tools

- `bin/voice-loop` — Continuous voice conversation helper for Claude Code
- `bin/whisper-upgrade` — Download better Whisper STT models (small/medium/large)
