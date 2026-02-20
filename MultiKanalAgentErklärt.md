# MultiKanal — Das komplette Projekt erklärt

> **Dein KI-Coding-Team redet jetzt mit dir.** MultiKanal verwandelt stumme Terminal-Ausgaben in gesprochene deutsche Audio-Kommentare — für jeden Agenten eine eigene Stimme.

---

## 1. Die große Idee

Stell dir vor, du hast vier Assistenten in einem Büro — Claude Code, OpenCode, Codex, Gemini. Alle arbeiten gleichzeitig, aber keiner sagt was. Du musst ständig auf den Bildschirm starren, um mitzubekommen was passiert.

**MultiKanal löst das:** Jeder Agent bekommt ein Mikrofon. Wenn Claude Code einen Bug fixt, *hörst du*: "Auth-Bug gefixt, drei Dateien angepasst. Login sollte jetzt stabil laufen." Und du erkennst an der Stimme, *welcher* Agent spricht.

---

## 2. Architektur — Wie das System aufgebaut ist

```
┌──────────────────────────────────────────────────┐
│              KI-Coding-Agenten                    │
│  Claude Code  │  OpenCode  │  Codex  │  Gemini  │
└──────┬─────────────┬──────────┬─────────┬────────┘
       │ Hook JSON   │ SSE      │ JSONL   │
       ▼             ▼          ▼         ▼
┌──────────────────────────────────────────────────┐
│      MultiKanal Daemon (Port 7742)               │
│      FastAPI + Uvicorn (async)                   │
│                                                   │
│  ┌──────────────────────────────────────────┐    │
│  │ 1. FILTER — Noise raus                   │    │
│  │    Code-Blöcke, Pfade, ANSI, URLs → weg  │    │
│  └──────────────────────────────────────────┘    │
│                    ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 2. CACHE CHECK — Schon mal gehört?       │    │
│  │    SHA256(text+voice) → .wav oder miss    │    │
│  └──────────────────────────────────────────┘    │
│                    ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 3. NARRATION — LLM fasst zusammen        │    │
│  │    MiniMax → Ollama → Template → Pass     │    │
│  │    System-Prompt: audio_prompt.md         │    │
│  │    (Watchdog → hot-reload ohne Restart)   │    │
│  └──────────────────────────────────────────┘    │
│                    ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 4. TTS — Text wird Audio                 │    │
│  │    Edge TTS → Piper → spd-say            │    │
│  │    Pro Agent eigene Stimme + Speed/Pitch  │    │
│  └──────────────────────────────────────────┘    │
│                    ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 5. AUDIO QUEUE — Einer nach dem anderen  │    │
│  │    asyncio.Queue(maxsize=5), FIFO         │    │
│  │    paplay → ffplay → aplay                │    │
│  └──────────────────────────────────────────┘    │
│                    ↓                              │
│  ┌──────────────────────────────────────────┐    │
│  │ 6. EVAL LOG — Qualität messen            │    │
│  │    info_density, filler_count, prompt_hash│    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
       │
       ▼  🔊 Lautsprecher
```

### Die 4 Schichten als Analogie

| Schicht | Rolle | Analogie |
|---------|-------|----------|
| **Adapter** | Fängt Agent-Output ab | Mikrofon an jedem Agenten |
| **Narration** | Kürzt auf 1-2 Sätze | Redakteur, der den Text strafft |
| **TTS** | Wandelt Text → Audio | Sprecher im Studio |
| **Playback** | Spielt ab, nie gleichzeitig | Regie, die Mikros schaltet |

---

## 3. Verzeichnisstruktur

```
AiSystemForVibeCoding/
├── bin/                              # CLI-Tools (Bash)
│   ├── ai                            # Kommando-Erklärer ("ai grep" → Power-User-Tipps)
│   └── ai-speak                      # Manuelles TTS-Frontend
│
├── config/                           # Konfiguration (hot-reloadable)
│   ├── default.yaml                  # Hauptconfig: Ports, Voices, Provider-Chain
│   └── audio_prompt.md               # Qualitätsregeln für Narrations
│
├── src/multikanal/                   # Python-Paket (pip install -e .)
│   ├── __main__.py                   # Entry: ruft cli.main() auf
│   ├── cli.py                        # Subcommands: daemon, narrate, health, stop...
│   ├── config.py                     # YAML-Loader mit .env-Injection
│   ├── daemon.py                     # ★ HERZSTÜCK: FastAPI-Server
│   │
│   ├── adapters/                     # Ein Adapter pro Agent
│   │   ├── base.py                   # Abstract: send_to_daemon(), _guess_language()
│   │   ├── claude_hook.py            # Claude Code Hook-Events verarbeiten
│   │   ├── codex_wrapper.py          # Codex JSONL-Stream wrappen
│   │   └── opencode_sse.py           # OpenCode SSE-Events empfangen
│   │
│   ├── narration/                    # Text → Deutsche Zusammenfassung
│   │   ├── generator.py              # Provider-Chain orchestrieren
│   │   ├── providers.py              # MiniMax, Ollama, Template, Passthrough
│   │   ├── claude_code.py            # Claude CLI als Narrations-Provider
│   │   ├── filter.py                 # Noise rausfiltern (Code, Pfade, URLs)
│   │   ├── eval_log.py               # Qualitätsmetriken → JSONL
│   │   ├── prompt.py                 # Watchdog: hot-reload audio_prompt.md
│   │   └── template.py              # 50+ statische Fallback-Templates
│   │
│   └── tts/                          # Zusammenfassung → Audio
│       ├── piper.py                  # Edge TTS / Piper / spd-say Engine
│       ├── cache.py                  # SHA256-basierter LRU-Cache
│       └── playback.py              # paplay / ffplay / aplay Abspieler
│
├── plugins/claude-hook/hooks/        # Claude Code Integration
│   ├── stop.py                       # Feuert bei Session-Ende
│   └── post_tool_use.py              # Feuert nach jedem Tool-Aufruf
│
├── systemd/multikanal.service        # Autostart als systemd User-Service
├── pyproject.toml                    # Dependencies & `multikanal` CLI Entry Point
├── .env.example                      # Template: MINIMAX_API_KEY=...
└── FOR_SMLFLG.md                     # Architektur-Doku
```

---

## 4. Deep Dive: Narration Pipeline

### Was passiert, wenn Text reinkommt

Die Narration Pipeline ist das Gehirn des Systems. Sie nimmt rohen Agent-Output und verwandelt ihn in einen knackigen deutschen Satz.

### 4.1 Filter (`narration/filter.py`)

**Problem:** Agent-Output ist voller Noise — ANSI-Codes, Code-Blöcke, Dateipfade, URLs, Diff-Header. Wenn du das einem LLM gibst, produziert es Müll.

**Lösung:** 7 Regex-Passes in fester Reihenfolge:

```python
# Reihenfolge ist wichtig!
1. ANSI-Escape-Codes      → weg (Farbcodes, Cursor-Steuerung)
2. Code-Fences ```...```   → "[code block removed]"
3. Inline-Code `...`       → weg
4. Tool-Call-JSON          → weg ({"tool": ...})
5. Diff-Header (---/+++/@@)→ weg
6. Diff-Zeilen (+/-)       → weg
7. Dateipfade (/foo/bar)   → weg
8. URLs (http://...)       → weg
9. Mehrfach-Leerzeilen     → eine Leerzeile
10. Truncate auf 2000 Zeichen (am Wortende)
```

**Warum?** Der LLM soll nur den *Inhalt* sehen, nicht den *Code*. "3 files changed, 47 insertions" ist nützlich. "```python\ndef foo():\n  pass\n```" ist Noise.

### 4.2 Generator (`narration/generator.py`)

**Das Chain-of-Responsibility Pattern:** Der Generator probiert Provider der Reihe nach durch, bis einer eine Antwort liefert.

```python
class NarrationGenerator:
    def generate(self, text, system_prompt, language):
        for provider in self.providers:
            try:
                narration = provider.generate(text, system_prompt, language)
            except Exception:
                pass  # Nächster Provider
            if narration:
                self.last_result = {"provider": provider.name, "latency_ms": ...}
                return narration
        return ""  # Alle gescheitert
```

**Konfigurierbar via YAML:** Welche Provider aktiv sind, in welcher Reihenfolge, mit welchen Timeouts — alles in `config/default.yaml`.

### 4.3 Provider im Detail (`narration/providers.py`)

#### MiniMax (Primär — schnell, online)
```
Endpoint: https://api.minimax.io/v1/chat/completions
Modell:   MiniMax-M2.1
Timeout:  6 Sekunden
Kosten:   ~$0.15/1M tokens
```

**Wie es funktioniert:**
1. System-Prompt (aus `audio_prompt.md`) + User-Text → POST an API
2. Antwort parsen (multiple Response-Shapes werden unterstützt — MiniMax ändert sein Format gelegentlich)
3. `<think>`-Tags und Markdown-Formatierung rausstrippen → sauberer TTS-Text

**Robustheit:** Der Response-Parser probiert 6 verschiedene JSON-Pfade:
```python
choice.message.content → choice.delta.content → choice.messages[0].content
→ choice.output_text → data.text → data.content
```
MiniMax hat sein API-Format schon mehrfach geändert. Dieser Parser überlebt das.

#### Ollama (Fallback — langsam, lokal)
```
Endpoint: http://localhost:11434/api/generate
Modelle:  llama3.1:8b → phi4 → mistral-nemo (der Reihe nach)
Timeout:  10 Sekunden
Kosten:   Gratis (nur Strom)
```

**Prompt auf Deutsch:**
```
Agent-Ausgabe:
{text}

Erstelle eine Audio-Erklärung (maximal 80 Wörter).
```

Probiert 3 Modelle der Reihe nach. Wenn das erste Modell nicht installiert ist → nächstes.

#### Template (Not-Fallback — instant, statisch)
Kein LLM nötig. Nimmt den gefilterten Text, kürzt auf max_words, stellt "Kurze Zusammenfassung:" voran. Qualität mäßig, aber immer verfügbar.

#### Passthrough (Letzter Ausweg)
Gibt den Input-Text direkt zurück, gekürzt auf max_words. Kein LLM, kein Template. Einfach durchreichen.

### 4.4 Prompt Hot-Reload (`narration/prompt.py`)

**Das Problem:** Du willst den Narrations-Stil ändern ("weniger Füllwörter", "max 60 statt 40 Wörter"), ohne den Daemon neu zu starten.

**Die Lösung:** `PromptWatcher` nutzt die `watchdog`-Library:

```python
class PromptWatcher:
    def __init__(self, prompt_path):
        self._path = Path(prompt_path)
        self._prompt = ""
        self._lock = threading.Lock()  # Thread-safe!
        self._load()  # Sofort laden

    def start(self):
        # Watchdog Observer überwacht das config-Verzeichnis
        observer = Observer()
        observer.schedule(Handler(), str(self._path.parent))
        observer.daemon = True  # Stirbt mit dem Daemon
        observer.start()
```

**Ablauf:**
1. Daemon startet → `prompt.py` liest `config/audio_prompt.md`
2. Watchdog überwacht das Verzeichnis
3. Du editierst die Datei (z.B. "max 40 Wörter" → "max 60 Wörter")
4. OS feuert inotify-Event → Watchdog Handler → `_load()` wird aufgerufen
5. Nächste Narration nutzt den neuen Prompt
6. Thread-Lock verhindert Race Conditions beim Lesen

**Fallback:** Wenn `watchdog` nicht installiert ist, funktioniert alles trotzdem — nur ohne Auto-Reload. Du müsstest den Daemon neu starten.

### 4.5 Eval-Logging (`narration/eval_log.py`)

**Warum?** Du willst *messen*, ob deine Prompt-Änderungen die Narrations besser machen. Bauchgefühl reicht nicht.

**Was geloggt wird (JSONL, eine Zeile pro Narration):**

```json
{
  "ts": "2026-02-18T14:32:07Z",
  "source": "claude_code",
  "provider": "minimax",
  "in_chars": 847,
  "out_chars": 142,
  "out_words": 23,
  "prompt_hash": "a3f2c1e8",
  "llm_ms": 2847,
  "filler_count": 0,
  "starts_filler": false,
  "info_density": 0.78,
  "compression": 5.96,
  "input_preview": "Modified 3 files...",
  "narration": "Drei Dateien angepasst, Auth-Modul läuft jetzt stabil."
}
```

**Die Metriken erklärt:**

| Metrik | Was sie misst | Gut | Schlecht |
|--------|--------------|-----|---------|
| `info_density` | Anteil Inhaltswörter vs. Stoppwörter | >0.7 | <0.5 |
| `filler_count` | Verbotene Phrasen ("Es wurde", "Grundsätzlich") | 0 | >1 |
| `starts_filler` | Beginnt mit Füllphrase? | false | true |
| `compression` | Input-Chars / Output-Chars | >3.0 | <1.5 |

**Stoppwörter-Liste:** 100+ deutsche Funktionswörter (der, die, das, und, oder, aber...) die nicht als "Inhalt" zählen.

**`prompt_hash`:** SHA256 der ersten 8 Hex-Zeichen des System-Prompts. Damit kannst du filtern: "Zeig mir alle Narrations von Prompt-Version a3f2c1e8 vs. 7b4e9f12" → A/B-Testing.

---

## 5. Deep Dive: Hook-System

### Die eiserne Regel

> **Hooks blockieren NIE den Agenten.** Egal was passiert — `sys.exit(0)`.

Jeder Hook ist in einen doppelten try/except gewickelt. Wenn der Daemon nicht läuft? Exit 0. Wenn JSON-Parsing fehlschlägt? Exit 0. Wenn HTTP timeout? Exit 0. Der Agent merkt nichts.

### 5.1 PostToolUse Hook (`plugins/claude-hook/hooks/post_tool_use.py`)

**Trigger:** Feuert *nach jedem Tool-Aufruf* in Claude Code — Bash, Edit, Write, etc.

**Der Ablauf:**

```
Claude Code führt ein Tool aus (z.B. Bash: "git commit")
    ↓
Claude Code schreibt Event-JSON auf stdin des Hooks:
{
  "tool_name": "Bash",
  "tool_input": {"command": "git commit -m 'fix auth'", "description": "Commit changes"},
  "tool_response": {"stdout": "3 files changed, 47 insertions(+)"}
}
    ↓
Hook liest JSON, prüft:
  - tool_name in SKIP_TOOLS? (Read, Glob, Grep, WebSearch, WebFetch → ignorieren)
  - Nein? → Weiter
    ↓
Extrahiert Text aus tool_response:
  - Probiert: content → text → output → stdout → result
  - Für Bash: stdout ist der Hauptoutput
    ↓
Baut Kontext dazu:
  - Hat tool_input.description? → Nutze das als Kontext
  - Sonst: "Command: git commit -m 'fix auth'"
    ↓
Kombiniert: "Commit changes\n\nResult:\n3 files changed, 47 insertions(+)"
    ↓
HTTP POST an localhost:7742/narrate (Timeout: 2 Sekunden)
  {"text": "...", "source": "claude_code"}
    ↓
Sofort exit 0 (wartet nicht auf Antwort!)
```

**Warum diese Tools übersprungen werden:**
- `Read` — Gibt Dateiinhalt zurück → riesig, irrelevant zum Vorlesen
- `Glob` — Gibt Dateilisten zurück → Noise
- `Grep` — Gibt Suchergebnisse zurück → zu technisch
- `WebSearch/WebFetch` — Gibt Webinhalte zurück → zu lang

**Technisches Detail:** Der Hook nutzt `http.client` statt `httpx` oder `requests` — **null externe Dependencies**. Das ist Absicht: Hooks müssen instant starten, ohne `import httpx` (was ~100ms dauert).

### 5.2 Stop Hook (`plugins/claude-hook/hooks/stop.py`)

**Trigger:** Feuert wenn Claude Code eine Session beendet (letzte Antwort fertig).

**Der Ablauf:**

```
Claude Code beendet Session
    ↓
Stop-Event auf stdin:
{
  "stop_hook_active": false,
  "transcript_path": "/tmp/claude-transcript-abc123.jsonl"
}
    ↓
Prüft: stop_hook_active? → true = Exit (Loop-Prevention!)
    ↓
Liest Transcript JSONL rückwärts (letzte 50 Zeilen):
  - Sucht nach role: "assistant"
  - Extrahiert Text-Content (kann String oder Array von Blöcken sein)
    ↓
Truncate auf 3000 Zeichen
    ↓
HTTP POST: {"text": "...", "source": "claude_stop"}
    ↓
Exit 0
```

**Loop-Prevention:** Ohne `stop_hook_active`-Check würde passieren:
1. Claude Code antwortet → Stop Hook feuert
2. Daemon narrates → Claude Code sieht das als neue Aktivität?
3. Neuer Stop Hook → endlos

Der `stop_hook_active`-Flag verhindert das.

**Transcript-Parsing:** Der JSONL-Parser ist defensiv programmiert — er probiert zwei Formate:
```python
# Format 1: Direkt
{"role": "assistant", "content": "Text..."}

# Format 2: Gewrappt
{"message": {"role": "assistant", "content": [{"type": "text", "text": "..."}]}}
```

---

## 6. Deep Dive: TTS & Audio

### 6.1 Stimmen-Zuordnung — Jeder Agent hat eine Persönlichkeit

```
Claude Code  → Florian (de-DE-FlorianMultilingualNeural)
                Ruhig, neutral, der "Standard-Kollege"

OpenCode     → Conrad (de-DE-ConradNeural)
                Energisch, +5% Speed, für Live-Updates

Codex        → Seraphina (de-DE-SeraphinaMultilingualNeural)
                Kreativ, +2Hz Pitch

Gemini       → Killian (de-DE-KillianNeural)
                Analytisch

Englisch     → Aria (en-US-AriaNeural)
```

**Warum verschiedene Stimmen?**
Stell dir vor, 3 Leute reden in einem Raum. Wenn alle die gleiche Stimme hätten, wüsstest du nicht, wer spricht. Mit verschiedenen Stimmen weißt du *unterbewusst*, wer gerade dran ist — ohne auf den Bildschirm zu schauen.

**Per-Voice Tuning:**
```yaml
voice_settings:
  claude_code:  { rate: "+0%",  pitch: "+0Hz" }   # Baseline
  opencode:     { rate: "+5%",  pitch: "+0Hz" }   # Etwas schneller
  opencode_live:{ rate: "+8%",  pitch: "+0Hz" }   # Live-Updates noch schneller
  codex:        { rate: "+0%",  pitch: "+2Hz" }   # Etwas höher
```

### 6.2 TTS Engine Chain (`tts/piper.py`)

**3-Stufen-Fallback, wie bei der Narration:**

#### Stufe 1: Edge TTS (Microsoft, online, beste Qualität)
```python
async def _save():
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(outpath)

asyncio.run(_save())  # Sync-Wrapper um async Edge TTS
```

- Nutzt Microsoft Azure Neural Voices (kostenlos!)
- Rate und Pitch pro Voice konfigurierbar
- Produziert .wav Dateien
- Braucht Internet

#### Stufe 2: Piper (lokal, offline, Open Source)
```python
cmd = ["piper", "--model", "de-de-thorsten-medium.onnx", "--output_file", "out.wav"]
subprocess.run(cmd, input=text.encode(), timeout=30)
```

- Nur wenn .onnx Modelldatei vorhanden
- Thorsten-Modell für Deutsch
- `length_scale` steuert Geschwindigkeit (1/speed)
- Braucht kein Internet

#### Stufe 3: spd-say (Systemfallback, niedrigste Qualität)
```python
cmd = ["/usr/bin/spd-say", "-w", outpath, "-r", rate, "-p", "50", "-l", "de", text]
```

- Speech Dispatcher (Linux-Standard)
- Klingt robotisch, aber funktioniert immer
- Letzter Ausweg

### 6.3 Audio-Cache (`tts/cache.py`)

**Problem:** TTS ist langsam (~1-3s pro Narration). Wenn der gleiche Text nochmal kommt, will man nicht wieder warten.

**Lösung:** SHA256-basierter LRU-Cache.

```python
# Cache-Key = SHA256(text + "|" + voice)
# Selber Text mit anderer Stimme = anderer Cache-Eintrag

def get(text, voice):
    key = sha256(text + "|" + voice)
    path = ~/.cache/multikanal/{key}.wav
    if path.exists():
        path.touch()  # LRU: Access-Time aktualisieren
        return path
    return None

def put(text, voice, wav_path):
    key = sha256(text + "|" + voice)
    shutil.copy2(wav_path, ~/.cache/multikanal/{key}.wav)
    evict_if_needed()  # Wenn > 500 Einträge: älteste löschen
```

**LRU-Eviction:**
- Max 500 .wav-Dateien im Cache
- Wenn voll: sortiere nach Access-Time, lösche die ältesten
- `path.touch()` bei jedem `get()` → oft genutzte Dateien überleben

**Praktischer Effekt:** "Tests bestanden" nach dem dritten Mal = instant Playback (0ms statt 2000ms).

### 6.4 Playback (`tts/playback.py`)

**Auch hier: Fallback-Chain.**

```
paplay (PulseAudio-native, beste Integration)
  → ffplay (FFmpeg, universell)
    → aplay (ALSA-direkt, Basis)
```

**Features:**
- **PulseAudio Sink Selection:** `PULSE_SINK` Environment-Variable → Audio an bestimmten Ausgang
- **Volume Control:** 0.1 bis 2.0 (normalisiert auf paplay: 3277–65536, ffplay: 5–100)
- **Non-blocking:** `subprocess.Popen` + `wait()` → blockiert nur den Queue-Worker, nicht den Daemon

### 6.5 Audio Queue (im Daemon)

```python
_audio_queue = asyncio.Queue(maxsize=5)

async def _audio_queue_worker():
    while True:
        wav_path, audio_cfg = await _audio_queue.get()
        await asyncio.to_thread(_player.play, wav_path, sink, volume)
        _audio_queue.task_done()
```

**Warum eine Queue?**
- Ohne Queue: 3 Narrations kommen gleichzeitig → 3 Stimmen gleichzeitig → Chaos
- Mit Queue: FIFO, eine nach der anderen, maximal 5 warten
- Queue voll? → Narration wird übersprungen (besser als endlos wachsende Queue)

### 6.6 Der komplette Audio-Pfad

```
"3 files changed, 47 insertions" (Claude Code Output)
    ↓
[Filter] → "3 files changed, 47 insertions"
    ↓
[Cache Check] → Miss
    ↓
[MiniMax LLM] + audio_prompt.md System-Prompt
    → "Drei Dateien angepasst, Login sollte jetzt stabil laufen."
    ↓
[Eval Log] → {"info_density": 0.78, "filler_count": 0, ...}
    ↓
[Prefix] → "BepBup: Drei Dateien angepasst, Login sollte jetzt stabil laufen."
    ↓
[Edge TTS] → Florian-Stimme, rate=+0%, pitch=+0Hz → /tmp/multikanal_abc.wav
    ↓
[Cache Put] → ~/.cache/multikanal/sha256hash.wav
    ↓
[Audio Queue] → Warte bis vorheriges Audio fertig
    ↓
[paplay] → Lautsprecher 🔊
```

---

## 7. Technologie-Stack

| Komponente | Tech | Warum diese? |
|-----------|------|-------------|
| HTTP-Server | **FastAPI** + **Uvicorn** | Async-first, auto-Validierung via Pydantic, schnell |
| HTTP-Client | **HTTPX** | Async + Sync, moderne API, gutes Error Handling |
| Config | **PyYAML** + **.env** | YAML für Struktur, .env für Secrets (getrennt!) |
| File-Watch | **Watchdog** | OS-native Events (inotify auf Linux), robust |
| TTS primär | **Edge TTS** | Kostenlos, Neuralvoices, 10+ deutsche Stimmen |
| TTS fallback | **Piper** | Offline, ONNX-basiert, Open Source |
| LLM primär | **MiniMax M2.1** | Billig (~$0.15/1M tokens), schnell (~3s) |
| LLM fallback | **Ollama** | Gratis, lokal, kein Internet nötig |
| Audio | **PulseAudio** (paplay) | Linux-Standard, Sink-Routing, Volume-Control |
| Prozess-Mgmt | **systemd** | User-Service, Autostart, Journal-Logging |

---

## 8. Kosten

| Was | Kosten | Wann |
|-----|--------|------|
| MiniMax Narration | ~$0.008 / Aufruf | Pro Tool-Ergebnis |
| Edge TTS | $0 | Immer |
| Ollama | $0 (Strom) | Nur Fallback |
| Piper | $0 | Nur Fallback |
| **Gesamt (~100 Narrations/Tag)** | **~$0.50/Monat** | |

---

## 9. Stärken & Schwächen

### Stärken
- **Fail-Soft auf jeder Ebene** — 4 LLM-Fallbacks, 3 TTS-Fallbacks, 3 Playback-Fallbacks
- **Nie blockiert** — Hooks exit sofort, Daemon ist async, Queue verhindert Overlap
- **Messbar** — Eval-Logging macht Prompt-Tuning datengetrieben statt Bauchgefühl
- **Hot-Reload** — Prompt ändern = sofort aktiv, kein Neustart
- **Multi-Agent-Aware** — Jeder Agent eigene Stimme, eigene Speed/Pitch-Settings
- **Günstig** — Unter $1/Monat bei normalem Gebrauch

### Schwächen
- **MiniMax-Abhängigkeit** — Wenn API-Key ungültig UND Ollama nicht läuft → nur Templates
- **Prompt-Tuning = Kunst** — Funktioniert am besten auf Deutsch
- **OpenCode SSE** — Keine automatische Reconnection bei Server-Neustart (manueller Workaround: Polling)
- **Keine Queue-Persistenz** — Daemon-Crash = wartende Narrations verloren
- **Edge TTS braucht Internet** — Offline nur mit Piper (schlechtere Qualität)
