# TUI Voice Integration Architecture

> How the unified TUI becomes a voice-first coding environment — without depending on any
> single STT/TTS vendor, and without breaking the keyboard-only workflow for everyone else.

---

## System Diagram — Full Audio Pipeline

```
                         ┌─────────────────────────────────────────────────┐
                         │              AUDIO PIPELINE                      │
                         │                                                   │
  [Microphone]           │   STT Layer            TUI Core         TTS Layer │
       │                 │      │                    │                 │      │
       ▼                 │      ▼                    ▼                 ▼      │
  push-to-talk key       │  Whisper (local)    Intent Router    Edge TTS      │
  or wake word           │  Deepgram API   ──► Skill Dispatch   port 5050     │
       │                 │  Web Speech API     Command Parser   Florian/Katja │
       │                 │      │                    │                 │      │
       ▼                 │      ▼                    ▼                 ▼      │
  AudioCapture           │  Transcript        /skill X args     MP3 audio     │
  (pyaudio/sounddevice)  │  text string       or free-form      bytes         │
                         │      │             LLM message            │        │
                         │      └────────────────────────────────────┘        │
                         │                        │                           │
                         └────────────────────────┼───────────────────────────┘
                                                  │
                                        ┌─────────▼──────────┐
                                        │   Backend Agent      │
                                        │ (Claude/Codex/OC)    │
                                        └─────────┬───────────┘
                                                  │ response
                                        ┌─────────▼──────────┐
                                        │   TUI Event Bus      │
                                        │ post_tool_use        │
                                        │ session_stop         │
                                        └─────────┬───────────┘
                                                  │
                                        ┌─────────▼──────────┐
                                        │  Narration Plugin    │
                                        │  smart filter        │
                                        │  queue + priority    │
                                        └─────────┬───────────┘
                                                  │ POST /v1/audio/speech
                                        ┌─────────▼───────────┐
                                        │  Edge TTS Server     │
                                        │  localhost:5050      │
                                        │  (OpenAI-compatible) │
                                        └─────────┬───────────┘
                                                  │ MP3
                                                  ▼
                                             [Speakers]
```

---

## 1. TTS Output — Existing Daemon, Native TUI Widget

### 1.1 What Exists

The Edge TTS server (`voicemode-edge-tts/server.py`) runs on `localhost:5050` and exposes
an **OpenAI-compatible** `/v1/audio/speech` endpoint. It wraps Microsoft Edge TTS for
~1.5s synthesis latency, zero cost, and excellent German voices (Florian, Katja, Seraphina).

The current narration daemon on port **7742** (MultiKanalAgent) acts as a queue manager
on top of the TTS server. The TUI narration plugin (from `TUI_EVENTS.md`) fires POSTs to
port 7742.

**Correction/clarification:** The task description mentions port 7742 as the narration
endpoint. The `server.py` in `voicemode-edge-tts/` runs on port **5050** (OpenAI-compatible
API). Port 7742 is the higher-level narration queue daemon that likely calls 5050 internally.
The TUI design respects both layers.

### 1.2 TUI Narration Widget

The TUI renders a persistent status bar widget showing the narration queue state:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  VOICE  ▶ Florian  [██░░░░] 1.2s  │  Queue: 2  │  [P] Pause  [>] 1.5x  │
└─────────────────────────────────────────────────────────────────────────┘
```

Widget state machine:

```
IDLE ──(narration queued)──► PLAYING ──(audio done)──► IDLE
  │                              │
  │                           (P key)
  │                              ▼
  │                           PAUSED ──(P key)──► PLAYING
  │
  └──(queue > 0, paused)──► PAUSED
```

**Keybindings for the narration widget:**

| Key | Action |
|-----|--------|
| `Ctrl+P` | Toggle play/pause narration queue |
| `Ctrl+[` | Speed down (0.8x → 1.0x → 1.5x → 2.0x) |
| `Ctrl+]` | Speed up |
| `Ctrl+Backspace` | Clear narration queue (skip all pending) |
| `Ctrl+R` | Replay last narrated message |

### 1.3 Smart Narration Filter

Not everything the agent does should be narrated. The filter runs in the narration plugin
before any POST to the daemon:

```python
# Narration decision matrix

NEVER_NARRATE = {
    # Tool types that produce no useful audio
    "Read",        # File content dumps — too long, no signal
    "Glob",        # File list — read visually
    "Grep",        # Search results — read visually
    "WebSearch",   # Raw search results
    "WebFetch",    # Raw page content
    "TaskList",    # Internal bookkeeping
    "TaskGet",
}

ALWAYS_NARRATE = {
    # High-signal events
    "on_error",           # Something broke — tell the user
    "session_stop",       # Final assistant message
    "agent_complete",     # Background task done
    "focus_check",        # ADHS timer
    "context_degradation", # "Consider /compact"
}

# For post_tool_use on tools NOT in the above sets:
# Narrate IF result contains signal words:
SIGNAL_WORDS = [
    "error", "failed", "success", "done", "completed",
    "warning", "created", "deleted", "installed", "✓", "✗",
]
# Also narrate if result is SHORT (< 200 chars) — likely a status message
```

Priority levels sent to the narration daemon:

| Priority | When |
|----------|------|
| `1` (urgent) | `on_error`, session_stop with errors |
| `2` (normal) | Completion messages, agent_complete |
| `3` (low) | Background narration, focus_check |

Queue behavior: if queue length > 3 and new item is priority 3, drop it. The user is
already behind.

### 1.4 Voice Selection and Speed Control

The TUI config exposes voice preferences:

```toml
[voice.tts]
engine = "edge-tts"           # "edge-tts" | "openai" | "kokoro"
tts_url = "http://127.0.0.1:5050/v1"
voice = "florian"             # See voicemode-edge-tts VOICE_MAP
speed = 1.0                   # Default; user adjustable via Ctrl+[/]
language = "de"               # Preferred language for multilingual voices
narration_daemon_port = 7742  # MultiKanalAgent port

# Per-event voice overrides (optional)
[voice.tts.overrides]
on_error = {voice = "katja", speed = 1.2}  # Different voice for errors
focus_check = {voice = "florian", speed = 0.9}  # Slower for reminders
```

---

## 2. STT Input — New, Three Implementation Options

### 2.1 Option Comparison

| Option | Latency | Cost | Privacy | Quality | Setup |
|--------|---------|------|---------|---------|-------|
| **Whisper (local)** | ~1-3s (small), ~5s (large) | Free | 100% local | Good-Excellent | pip install openai-whisper |
| **Deepgram** | ~200ms | ~$0.0043/min | Cloud | Excellent | API key |
| **Web Speech API** | ~500ms | Free | Google cloud | Good | Browser only |

**Recommendation for this project:** Whisper small model as default. It runs on CPU with
~1s latency for typical voice commands (5-10 seconds of audio). No API key, no privacy
concern. Deepgram as opt-in for users who want near-real-time latency.

**Web Speech API is not applicable** — this is a terminal TUI, not a browser. Excluded.

### 2.2 Whisper Integration

```python
# tui/voice/stt.py

import asyncio
import queue
import threading
import numpy as np
import sounddevice as sd
import whisper

class WhisperSTT:
    """Local Whisper STT with push-to-talk or always-on mode."""

    SAMPLE_RATE = 16000   # Whisper expects 16kHz
    CHUNK_SIZE  = 1024    # ~64ms per chunk

    def __init__(self, model_size: str = "small", language: str = "de"):
        self.model = whisper.load_model(model_size)
        self.language = language
        self._recording = False
        self._audio_buf: list[np.ndarray] = []

    def start_recording(self):
        """Begin buffering audio (called on push-to-talk keydown)."""
        self._audio_buf.clear()
        self._recording = True

    def stop_recording(self) -> str:
        """Stop buffering and transcribe (called on push-to-talk keyup)."""
        self._recording = False
        if not self._audio_buf:
            return ""
        audio = np.concatenate(self._audio_buf)
        result = self.model.transcribe(
            audio,
            language=self.language,
            fp16=False,  # CPU-safe
        )
        return result["text"].strip()

    def _audio_callback(self, indata, frames, time, status):
        if self._recording:
            self._audio_buf.append(indata[:, 0].copy())
```

### 2.3 Deepgram Integration (opt-in)

```python
# tui/voice/stt_deepgram.py

import asyncio
import websockets
import json
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

class DeepgramSTT:
    """Streaming STT via Deepgram API. Near-real-time (~200ms)."""

    def __init__(self, api_key: str, language: str = "de"):
        self.client = DeepgramClient(api_key)
        self.language = language
        self._transcript_parts: list[str] = []

    async def transcribe_utterance(self) -> str:
        """Record and transcribe one utterance (push-to-talk)."""
        options = LiveOptions(
            model="nova-2",
            language=self.language,
            punctuate=True,
            endpointing=500,  # ms of silence to end utterance
        )
        # ... websocket streaming implementation
        return " ".join(self._transcript_parts)
```

### 2.4 Push-to-Talk vs Always-On

**Push-to-talk (default):**
- User holds `Ctrl+Space` to record
- Release to transcribe and submit
- Clear visual indicator: TUI status bar shows `[REC] ...` while held
- No false activations, no background noise issues
- Works well for deliberate voice commands

**Always-on with wake word (v2, optional):**
- Keyword: "Hey Agent" (Porcupine, pvporcupine library)
- After wake word: 5-second recording window
- Suitable for hands-free workflows
- Risk: false activations in noisy environments
- Not recommended as default — opt-in in config

```toml
[voice.stt]
engine = "whisper"            # "whisper" | "deepgram"
model = "small"               # Whisper model size
language = "de"               # Primary language
mode = "push_to_talk"         # "push_to_talk" | "always_on"
wake_word = "hey agent"       # Only for always_on mode
push_to_talk_key = "ctrl+space"

[voice.stt.deepgram]
api_key = ""                  # Set to enable Deepgram
model = "nova-2"
```

---

## 3. Voice → Text → Skill Invocation Pipeline

### 3.1 Intent Router

After STT produces a transcript, the TUI routes it through three layers:

```
Transcript: "Hey, research the new Textual 3 changelog"
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  Layer 1: Exact skill match (keyword prefix)         │
│  "research X" → /research X                          │
│  "focus on X" → /focus X                             │
│  "quickwin"   → /quickwin                            │
└─────────────────────────────────────────────────────┘
      │ (no match)
      ▼
┌─────────────────────────────────────────────────────┐
│  Layer 2: Fuzzy skill match (NLP patterns)           │
│  "ask the cheap model about X" → /research X         │
│  "run a quick win" → /quickwin                        │
│  "what did we change?" → /recap                      │
│  "check the state" → /check-state                    │
└─────────────────────────────────────────────────────┘
      │ (no match)
      ▼
┌─────────────────────────────────────────────────────┐
│  Layer 3: Free-form LLM message                      │
│  Send transcript directly as user message            │
│  to the current backend session                      │
└─────────────────────────────────────────────────────┘
```

### 3.2 Voice → Skill Mapping Table

| Voice Pattern | Dispatches To | Notes |
|---------------|---------------|-------|
| `"research [X]"` | `/research X` | Gemini research skill |
| `"ask Gemini [about X]"` | `/research X` | |
| `"focus on [X]"` | `/focus X` | Starts ADHS focus timer |
| `"quick win"` | `/quickwin` | |
| `"big win"` | `/bigwin` | |
| `"checkpoint"` | `/checkpoint` | |
| `"what did we change"` | `/recap` | |
| `"recap"` | `/recap` | |
| `"check state"` | `/check-state` | |
| `"review"` | `/review` | |
| `"commit"` | `/commit` | **Requires confirmation** |
| `"push"` | — | Blocked, say "use git push manually" |
| `"delegate [X]"` | `/chef X` | |
| `"run quickwin"` | `/quickwin` | |
| `"compact"` | `/compact` | |
| `"pause voice"` | TUI: pause narration | Internal TUI action |
| `"stop listening"` | TUI: disable STT | Internal TUI action |

### 3.3 Intent Router Implementation

```python
# tui/voice/intent_router.py

import re
from dataclasses import dataclass
from typing import Callable

@dataclass
class RouteResult:
    kind: str          # "skill" | "message" | "tui_action"
    value: str         # Skill name+args, message text, or action name
    confidence: float  # 0.0-1.0
    requires_confirm: bool = False

# Destructive actions always require TTS confirmation before dispatch
DESTRUCTIVE_SKILLS = {"commit", "push", "deploy", "delete"}

EXACT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^(hey agent[,.]?\s*)?research\s+(.+)$", re.I), "/research {2}"),
    (re.compile(r"^(hey agent[,.]?\s*)?ask (gemini|the cheap model)\s*(about\s+)?(.+)$", re.I), "/research {4}"),
    (re.compile(r"^(hey agent[,.]?\s*)?focus\s+on\s+(.+)$", re.I), "/focus {2}"),
    (re.compile(r"^(hey agent[,.]?\s*)?(quick[- ]?win)$", re.I), "/quickwin"),
    (re.compile(r"^(hey agent[,.]?\s*)?(big[- ]?win)$", re.I), "/bigwin"),
    (re.compile(r"^(hey agent[,.]?\s*)?checkpoint$", re.I), "/checkpoint"),
    (re.compile(r"^(hey agent[,.]?\s*)?(what did we (just )?change\??|recap)$", re.I), "/recap"),
    (re.compile(r"^(hey agent[,.]?\s*)?check state$", re.I), "/check-state"),
    (re.compile(r"^(hey agent[,.]?\s*)?review$", re.I), "/review"),
    (re.compile(r"^(hey agent[,.]?\s*)?commit$", re.I), "/commit"),
    (re.compile(r"^(hey agent[,.]?\s*)?(delegate|chef)\s+(.+)$", re.I), "/chef {3}"),
    (re.compile(r"^(hey agent[,.]?\s*)?compact$", re.I), "/compact"),
    (re.compile(r"^(hey agent[,.]?\s*)?pause (voice|narration)$", re.I), "TUI:pause_narration"),
    (re.compile(r"^(hey agent[,.]?\s*)?stop listening$", re.I), "TUI:disable_stt"),
]

def route(transcript: str) -> RouteResult:
    text = transcript.strip()
    for pattern, template in EXACT_PATTERNS:
        m = pattern.match(text)
        if m:
            # Fill template group references
            value = re.sub(r'\{(\d+)\}', lambda x: m.group(int(x.group(1))) or "", template)
            skill_name = value.lstrip("/").split()[0] if value.startswith("/") else ""
            is_destructive = skill_name in DESTRUCTIVE_SKILLS
            return RouteResult(
                kind="tui_action" if value.startswith("TUI:") else "skill",
                value=value,
                confidence=0.95,
                requires_confirm=is_destructive,
            )
    # No match → free-form message
    return RouteResult(kind="message", value=text, confidence=0.5)
```

### 3.4 Confirmation Flow for Destructive Actions

When `requires_confirm=True`, the TUI pauses, narrates the action, and waits for
verbal or keyboard confirmation before dispatching:

```
User says: "commit"
   │
   ▼
TTS narrates: "Soll ich einen Commit erstellen? Sage 'ja' oder drücke Enter."
   │
   ▼
TUI shows overlay:
┌──────────────────────────────────────┐
│  Destructive action: /commit          │
│                                       │
│  [Enter] Confirm   [Esc] Cancel       │
│  [V] Listen for voice ("ja"/"nein")   │
└──────────────────────────────────────┘
   │
   ├── "ja" / Enter → dispatch /commit
   └── "nein" / Esc → cancel, narrate "Abgebrochen."
```

---

## 4. Conversation Mode

### 4.1 What It Is

Conversation mode is a voice-first dialogue loop where the user speaks naturally about
code, the agent responds, and the TUI narrates the response. Unlike single-shot voice
commands, conversation mode maintains context across multiple turns.

### 4.2 Context Awareness

The agent already knows the session context. In conversation mode, the TUI enriches
each voice message with additional context before submitting:

```python
# tui/voice/conversation.py

def build_context_prefix(session: TUISession) -> str:
    """Build a short context header prepended to the user's voice message."""
    parts = []

    # Current file (if any editor focus)
    if session.focused_file:
        parts.append(f"[Current file: {session.focused_file}]")

    # Git state (short)
    git_summary = session.git_summary  # e.g. "on main, 3 uncommitted changes"
    if git_summary:
        parts.append(f"[Git: {git_summary}]")

    # Session goal (if /focus active)
    if session.focus_goal:
        parts.append(f"[Focus goal: {session.focus_goal}]")

    return " ".join(parts)
```

Example voice message after enrichment:

```
User says: "What did we just change?"

Submitted to agent:
  [Current file: tui/voice/stt.py] [Git: on feature/voice, 2 uncommitted changes]
  [Focus goal: Design voice integration]
  What did we just change?
```

### 4.3 Response Narration

When the agent responds in conversation mode, the narration plugin handles filtering
and dispatch. For conversation mode specifically, the filter is MORE permissive:
the agent's full text response is narrated (not just completion signals), up to 800
characters. Beyond that, the TUI truncates and says "... [response truncated, see
terminal]".

### 4.4 "What Did We Just Change?" Pattern

This is the canonical conversation mode use case. Implementation:

```python
@skill("what_did_we_change")
async def recap_changes(session: TUISession) -> str:
    """Read git diff, generate narrable summary."""
    diff = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        cwd=session.cwd, capture_output=True, text=True
    ).stdout.strip()

    if not diff:
        return "Keine uncommitteten Änderungen."

    # Send to agent with instruction to summarize for voice
    response = await session.send_message(
        f"Summarize these git changes in 2-3 sentences for voice narration:\n{diff}"
    )
    return response
```

---

## 5. Accessibility

### 5.1 Voice as Accessibility Feature

For users who cannot use a keyboard effectively (motor disabilities, RSI, etc.), voice
mode provides full TUI control:

- All skills are reachable via voice commands
- Navigation ("go to next section", "scroll down") maps to TUI actions
- Error messages are always narrated at priority 1
- The TUI never requires a mouse

### 5.2 Screen Reader Compatibility

The TUI uses Python Textual. Textual's DOM is not natively screen-reader-accessible
on terminals, but the TUI adds compensating measures:

- All important state changes emit via the narration plugin (the TUI IS the screen reader)
- A "describe current screen" voice command (`"what's on screen"`) narrates the current
  TUI panel contents
- Log output is appended to a plain-text file that external screen readers can monitor:
  `~/.config/myaigame-tui/voice_log.txt`

### 5.3 Keyboard-Only Navigation

All TUI functions are reachable without voice. The full keybinding table is the primary
interface; voice is an enhancement, not a requirement.

```
[Tab]          Focus next panel
[Shift+Tab]    Focus previous panel
[?]            Show keybinding help
[F1]           Toggle voice mode on/off
[F2]           Toggle narration on/off
[Ctrl+Space]   Push-to-talk (when voice on)
[Ctrl+P]       Pause/resume narration
[Ctrl+/]       Command palette (keyboard alternative to voice commands)
```

### 5.4 High Contrast Mode

```toml
[theme]
preset = "high_contrast"  # Options: "default" | "dark" | "high_contrast" | "solarized"
```

High contrast preset:
- Black background, white text
- Error messages: bright yellow
- Success: bright green
- Narration widget: bright cyan border
- No color gradients, no dim text

---

## 6. Voice Plugin Architecture

### 6.1 How It Fits in the TUI Event System

Voice is implemented as two TUI plugins that integrate with the existing event bus
(defined in `TUI_EVENTS.md`):

```
tui/plugins/
    narration.py    # Existing (TTS output) — enhanced with queue widget
    voice_input.py  # New (STT input) — handles mic capture and routing
```

`voice_input.py` runs a background thread for audio capture. When push-to-talk key is
pressed, the thread starts recording. On release, it calls `WhisperSTT.stop_recording()`,
routes the transcript through `IntentRouter`, and either:
- Dispatches a skill (inserts `/skill args` into TUI input and auto-submits)
- Sends a free-form message to the backend session
- Executes a TUI action directly (pause narration, toggle voice)

### 6.2 Plugin File: voice_input.py

```python
# ~/.config/myaigame-tui/plugins/voice_input.py

from tui_events import plugin, SessionStartEvent, SessionStopEvent
from tui.voice.stt import WhisperSTT
from tui.voice.intent_router import route, RouteResult
from tui.tui_state import get_current_session

stt: WhisperSTT | None = None

@plugin.on("session_start")
def init_voice(event: SessionStartEvent):
    global stt
    cfg = load_voice_config()
    if not cfg.get("stt", {}).get("enabled", False):
        return
    stt = WhisperSTT(
        model_size=cfg["stt"].get("model", "small"),
        language=cfg["stt"].get("language", "de"),
    )
    _narrate("Voice-Eingabe bereit. Strg+Leertaste zum Sprechen.", priority=3)

@plugin.on("session_stop")
def teardown_voice(event: SessionStopEvent):
    global stt
    stt = None

# Keybinding handlers are registered separately in the TUI keybinding system,
# not as event bus plugins — they call stt.start_recording() / stop_recording()
# and then route() the result.
```

### 6.3 Configuration

Full voice configuration in `~/.config/myaigame-tui/config.toml`:

```toml
[voice]
enabled = true

[voice.stt]
enabled = true
engine = "whisper"
model = "small"           # tiny | small | medium | large
language = "de"
mode = "push_to_talk"
push_to_talk_key = "ctrl+space"
# always_on settings (ignored when mode = push_to_talk)
wake_word = "hey agent"
silence_timeout_ms = 2000

[voice.stt.deepgram]
enabled = false
api_key = ""
model = "nova-2"

[voice.tts]
enabled = true
engine = "edge-tts"
tts_url = "http://127.0.0.1:5050/v1"
narration_daemon_url = "http://127.0.0.1:7742"
voice = "florian"
speed = 1.0
language = "de"
max_queue_length = 5
drop_low_priority_when_full = true

[voice.tts.overrides]
on_error = {voice = "katja", speed = 1.1}

[voice.narration_filter]
skip_tools = ["Read", "Glob", "Grep", "WebSearch", "WebFetch", "TaskList", "TaskGet"]
max_narration_chars = 800
always_narrate_errors = true
```

---

## 7. Implementation Phases

### Phase 1 — TTS Widget (low effort, existing daemon)
- Wrap existing narration daemon integration in the narration.py TUI plugin
- Add narration queue widget to TUI status bar
- Implement smart filter (NEVER_NARRATE / ALWAYS_NARRATE / SIGNAL_WORDS)
- Keybindings: Ctrl+P, Ctrl+[/], Ctrl+Backspace
- Voice selection and speed control in config

**Depends on:** Edge TTS server running on port 5050, narration daemon on 7742.
**Risk:** Low — the daemon already works.

### Phase 2 — STT Push-to-Talk (medium effort)
- Add `sounddevice` + `openai-whisper` dependencies
- Implement `WhisperSTT` class (push-to-talk mode)
- Add push-to-talk keybinding (Ctrl+Space)
- Visual recording indicator in TUI status bar
- Implement `IntentRouter` with exact pattern matching

**Risk:** Medium — depends on user's microphone setup and audio libraries.
**Mitigation:** Graceful degradation: if `sounddevice` import fails, voice input is
disabled with a warning, TTS still works.

### Phase 3 — Conversation Mode (medium effort)
- Context-aware message enrichment (`build_context_prefix`)
- "What did we change?" skill using git diff summary
- Destructive action confirmation overlay
- More permissive narration filter for conversation mode

### Phase 4 — Always-On Wake Word (low priority, optional)
- Integrate Porcupine wake word detection
- Configurable wake word
- Auto-disable after 30min idle
- Not recommended for default config

---

## 8. Open Questions

1. **Audio device selection:** `sounddevice` defaults to the system default mic. Should
   the TUI expose device selection in config, or trust the OS audio routing? Recommendation:
   Trust OS routing for now, add config in v2 if users ask.

2. **Whisper model download:** The `small` model is 461MB. Should the TUI auto-download
   it on first use, or require manual setup? Recommendation: Prompt on first voice
   activation, offer download with progress bar.

3. **German/English mixing:** Florian is multilingual but Whisper's language hint affects
   transcription quality. Should the TUI auto-detect language per utterance or use a fixed
   language? Recommendation: Fixed `de` by default, override per session with
   `voice language en`.

4. **TTS narration during agent thinking:** The agent sometimes takes 10-30 seconds to
   respond. Should the TUI narrate "Ich denke..." after 5 seconds of silence?
   Recommendation: Yes, with a configurable timeout (default 8s). This is an accessibility
   win for eyes-free use.

5. **Narration daemon dependency:** The current setup requires MultiKanalAgent on port 7742
   as a queue manager on top of the Edge TTS server on 5050. Should the TUI bypass the
   daemon and call the Edge TTS server directly? Recommendation: Keep the daemon for now
   (it handles queuing and priority), but design the narration plugin to fall back to
   direct TTS if the daemon is down.
