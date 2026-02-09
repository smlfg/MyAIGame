"""FastAPI daemon — receives agent output, generates narration, speaks it."""

import asyncio
import logging
import time
import re
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from .config import load_config
from .narration.filter import filter_output
from .narration.generator import NarrationGenerator
from .narration.prompt import PromptWatcher
from .tts.cache import AudioCache
from .tts.piper import PiperTTS
from .tts.playback import AudioPlayer

logger = logging.getLogger("multikanal.daemon")

# Global state
_config: dict[str, Any] = {}
_generator: NarrationGenerator | None = None
_tts: PiperTTS | None = None
_cache: AudioCache | None = None
_player: AudioPlayer | None = None
_prompt_watcher: PromptWatcher | None = None


class NarrateRequest(BaseModel):
    text: str
    source: str = "unknown"
    language: str = ""
    direct_tts: bool = False  # True = skip LLM, speak text directly


class NarrateResponse(BaseModel):
    status: str
    narration: str = ""
    cached: bool = False
    duration_ms: int = 0


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    providers: dict[str, bool]
    provider_chain: list[str]
    piper_available: bool
    opencode_connected: bool = False


_start_time: float = 0.0
_audio_queue: asyncio.Queue | None = None
_queue_worker_task: asyncio.Task | None = None
_narrate_lock: asyncio.Lock | None = None
_opencode_listener_task: asyncio.Task | None = None
_opencode_connected: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on startup, clean up on shutdown."""
    global _config, _generator, _tts, _cache, _player, _prompt_watcher, _start_time
    global _audio_queue, _queue_worker_task, _narrate_lock, _opencode_listener_task

    _start_time = time.monotonic()
    _config = load_config()

    # Mutex: only one narration pipeline runs at a time
    _narrate_lock = asyncio.Lock()

    # Audio queue: narrations play one after another, never overlapping
    _audio_queue = asyncio.Queue(maxsize=5)
    _queue_worker_task = asyncio.create_task(_audio_queue_worker())

    narr_cfg = _config.get("narration", {})
    tts_cfg = _config.get("tts", {})
    cache_cfg = _config.get("cache", {})

    _generator = NarrationGenerator.from_config(narr_cfg)

    _prompt_watcher = PromptWatcher(narr_cfg.get("prompt_file", ""))
    _prompt_watcher.start()

    _tts = PiperTTS(
        command=tts_cfg.get("command", ""),
        voices=tts_cfg.get("voices", {}),
        default_voice=tts_cfg.get("default_voice", "de"),
        speed=tts_cfg.get("speed", 1.0),
    )

    _cache = AudioCache(
        cache_dir=cache_cfg.get("path", "~/.cache/multikanal"),
        max_entries=cache_cfg.get("max_entries", 500),
    )

    _player = AudioPlayer(
        tool=_config.get("playback", {}).get("tool", ""),
    )

    # Optional: OpenCode SSE listener as background task
    oc_cfg = _config.get("adapters", {}).get("opencode_sse", {})
    if oc_cfg.get("enabled"):
        sse_url = oc_cfg.get("url", "http://localhost:3000/events")
        reconnect_delay = oc_cfg.get("reconnect_delay", 5)
        daemon_port = _config["daemon"]["port"]
        _opencode_listener_task = asyncio.create_task(
            _opencode_sse_listener(sse_url, daemon_port, reconnect_delay)
        )
        logger.info("OpenCode SSE listener enabled → %s", sse_url)
    else:
        logger.info("OpenCode SSE listener disabled (set enabled: true in config)")

    logger.info(
        "daemon started on %s:%d",
        _config["daemon"]["host"],
        _config["daemon"]["port"],
    )

    yield

    # Shutdown
    if _opencode_listener_task:
        _opencode_listener_task.cancel()
    if _queue_worker_task:
        _queue_worker_task.cancel()
    if _prompt_watcher:
        _prompt_watcher.stop()
    if _player:
        _player.stop()
    logger.info("daemon stopped")


app = FastAPI(title="MultiKanalAgent Daemon", version="0.1.0", lifespan=lifespan)


@app.post("/narrate", response_model=NarrateResponse)
async def narrate(req: NarrateRequest):
    """Receive agent output, generate narration, speak it."""
    t0 = time.monotonic()

    if not req.text.strip():
        return NarrateResponse(status="skipped", narration="", duration_ms=0)

    # Mutex: only one narration at a time — no overlapping speakers
    async with _narrate_lock:
        agent_voices = _config.get("tts", {}).get("agent_voices", {})
        voice_key = agent_voices.get(req.source) or req.language or _tts.default_voice
        audio_cfg = _config.get("audio", {})
        prefixes_cfg = audio_cfg.get("prefixes", {})

        # --- Direct TTS mode: skip LLM, speak text as-is ---
        if req.direct_tts:
            from .narration.providers import _clean_for_tts

            narration = _clean_for_tts(req.text.strip())
            if not narration:
                return NarrateResponse(status="skipped", narration="", duration_ms=0)

            if len(narration) > 1500:
                narration = narration[:1500]

            # ai_explain: remove flags/backticks for more natural speech
            if req.source == "ai_explain":
                narration = re.sub(r"`+", "", narration)
                narration = " ".join(
                    tok for tok in narration.split() if not tok.startswith("-")
                )
                narration = re.sub(r"\s+", " ", narration).strip()

            prefix = prefixes_cfg.get(req.source, "")
            audio_text = f"{prefix}{narration}" if prefix else narration

            voice_name = _tts.resolve_voice(voice_key)
            wav_path = await asyncio.to_thread(_tts.synthesize, audio_text, voice_name)
            if wav_path:
                await _play_audio(wav_path, audio_cfg)
                await _audio_queue.join()

            duration = int((time.monotonic() - t0) * 1000)
            return NarrateResponse(
                status="ok", narration=audio_text, cached=False, duration_ms=duration
            )

        # --- Normal mode: filter → LLM narration → TTS ---
        # Step 1: Filter the agent output
        filtered = filter_output(
            req.text,
            max_chars=_config.get("narration", {}).get("max_input_chars", 2000),
        )
        if not filtered.strip():
            return NarrateResponse(status="skipped", narration="", duration_ms=0)

        # Step 2: Cache lookup
        cached_path = _cache.get(filtered, voice_key)
        if cached_path:
            await _play_audio(cached_path)
            await _audio_queue.join()
            duration = int((time.monotonic() - t0) * 1000)
            return NarrateResponse(
                status="ok",
                narration="(cached)",
                cached=True,
                duration_ms=duration,
            )

        # Step 3: Generate narration via LLM
        system_prompt = _prompt_watcher.get_prompt() if _prompt_watcher else ""
        try:
            narration = await asyncio.wait_for(
                asyncio.to_thread(
                    _generator.generate, filtered, system_prompt, req.language
                ),
                timeout=_config.get("narration", {}).get("timeout_seconds", 25),
            )
        except asyncio.TimeoutError:
            narration = ""
        if not narration:
            duration = int((time.monotonic() - t0) * 1000)
            return NarrateResponse(
                status="no_narration", narration="", duration_ms=duration
            )

        # Step 4: Prefix & Synthesize TTS
        if req.source in prefixes_cfg:
            prefix = prefixes_cfg[req.source]
        elif req.source == "claude_stop":
            prefix = audio_cfg.get("stop_prefix", "BepBup: ")
        else:
            prefix = audio_cfg.get("prefix", "")

        audio_text = f"{prefix}{narration}" if prefix else narration

        voice_name = _tts.resolve_voice(voice_key)
        wav_path = await asyncio.to_thread(_tts.synthesize, audio_text, voice_name)
        if wav_path:
            _cache.put(audio_text, voice_key, wav_path)
            await _play_audio(wav_path, audio_cfg)
            await _audio_queue.join()

        duration = int((time.monotonic() - t0) * 1000)
        return NarrateResponse(
            status="ok", narration=audio_text, cached=False, duration_ms=duration
        )


async def _opencode_sse_listener(
    sse_url: str, daemon_port: int, reconnect_delay: float = 5
):
    """Background task: connect to OpenCode SSE, forward events to /narrate.

    Falls SSE keine Message-Events liefert (TUI nutzt interne Verbindung),
    wird zusätzlich Polling auf Session API gemacht.
    """
    import httpx

    global _opencode_connected

    daemon_url = f"http://127.0.0.1:{daemon_port}"
    accumulated: list[str] = []
    last_message_ids: dict[str, str] = {}  # session_id -> last_message_id
    session_poll_interval = 3.0
    opencode_base_url = sse_url.replace("/global/event", "")
    poll_task: asyncio.Task | None = None

    async def poll_all_sessions(client):
        """Pollt alle aktiven Sessions für neue Nachrichten."""
        try:
            resp = await client.get(f"{opencode_base_url}/session", timeout=10.0)
            if resp.status_code != 200:
                return
            data = resp.json()
            sessions = data.get("data", {}).get("sessions", [])
            for session in sessions:
                session_id = session.get("id")
                if not session_id:
                    continue
                await check_session_messages(
                    client, session_id, daemon_url, opencode_base_url
                )
        except Exception as e:
            logger.debug("Session poll failed: %s", e)

    async def check_session_messages(
        client, session_id: str, daemon_url: str, base_url: str
    ):
        """Prüft neue Nachrichten in einer Session."""
        try:
            resp = await client.get(
                f"{base_url}/session/{session_id}/messages", timeout=10.0
            )
            if resp.status_code != 200:
                return
            messages = resp.json().get("data", {}).get("messages", [])
            if not messages:
                return

            last_id = last_message_ids.get(session_id)
            for msg in messages:
                msg_id = msg.get("id")
                if msg_id == last_id:
                    break
                if msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        text = " ".join(
                            [
                                b.get("text", "")
                                for b in content
                                if isinstance(b, dict) and b.get("type") == "text"
                            ]
                        )
                    else:
                        text = str(content)
                    if text:
                        await client.post(
                            f"{daemon_url}/narrate",
                            json={"text": text, "source": "opencode"},
                            timeout=30.0,
                        )
                        logger.info(f"OpenCode: narrated message from {session_id}")
            if messages:
                last_message_ids[session_id] = messages[-1].get("id", "")
        except Exception as e:
            logger.debug("Check messages failed: %s", e)

    async def run_poll_loop(client):
        """Führt Polling im Hintergrund aus."""
        while True:
            await poll_all_sessions(client)
            await asyncio.sleep(session_poll_interval)

    last_poll_time = 0.0

    while True:
        try:
            logger.info("OpenCode SSE: connecting to %s", sse_url)
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", sse_url) as response:
                    if response.status_code == 200:
                        _opencode_connected = True
                        logger.info("OpenCode SSE: connected ✓")

                    event_type = ""
                    async for line in response.aiter_lines():
                        current_time = asyncio.get_event_loop().time()

                        if current_time - last_poll_time >= session_poll_interval:
                            last_poll_time = current_time
                            asyncio.create_task(poll_all_sessions(client))

                        line_stripped = line.strip()
                        if line_stripped:
                            logger.debug(f"SSE received: {line_stripped[:100]}")

                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                            continue

                        if not line.startswith("data:"):
                            continue

                        raw_data = line[5:].strip()
                        text = _extract_opencode_text(event_type, raw_data)

                        if text:
                            accumulated.append(text)
                            try:
                                await client.post(
                                    f"{daemon_url}/narrate",
                                    json={"text": text, "source": "opencode_live"},
                                    timeout=30,
                                )
                            except Exception as e:
                                logger.debug("OpenCode live send failed: %s", e)

                        if event_type == "session.idle" and accumulated:
                            summary = "\n".join(accumulated)
                            accumulated.clear()
                            try:
                                await client.post(
                                    f"{daemon_url}/narrate",
                                    json={"text": summary, "source": "opencode_final"},
                                    timeout=60,
                                )
                            except Exception as e:
                                logger.debug("OpenCode final send failed: %s", e)

        except asyncio.CancelledError:
            _opencode_connected = False
            logger.info("OpenCode SSE listener stopped")
            break
        except Exception as e:
            _opencode_connected = False
            logger.info(
                "OpenCode SSE disconnected (%s), reconnecting in %ds",
                e,
                reconnect_delay,
            )
            await asyncio.sleep(reconnect_delay)



def _extract_opencode_text(event_type: str, raw_data: str) -> str:
    """Extract assistant text from an OpenCode SSE event.

    Events from /global/event have format:
    {"directory": "...", "payload": {"type": "...", "properties": {...}}}
    """
    import json as _json

    try:
        data = _json.loads(raw_data)
    except (_json.JSONDecodeError, TypeError):
        return ""

    payload = data.get("payload", {})
    actual_event_type = payload.get("type", event_type)
    properties = payload.get("properties", {})

    if actual_event_type == "session.idle":
        return ""

    if actual_event_type in ("message.created", "message.updated"):
        message_info = properties.get("info", {})
        if message_info.get("role") != "assistant":
            return ""
        content = message_info.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = [
                b.get("text", "")
                for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            ]
            return "\n".join(texts)

    if actual_event_type == "session.created":
        info = properties.get("info", {})
        title = info.get("title", "Neue Session")
        return f"OpenCode: Neue Session '{title}' erstellt."

    if actual_event_type == "session.updated":
        info = properties.get("info", {})
        title = info.get("title", "")
        if title:
            return f"OpenCode: Session '{title}' aktualisiert."
        return "OpenCode: Session aktualisiert."

    return ""


async def _audio_queue_worker():
    """Worker that plays audio files sequentially from the queue."""
    while True:
        try:
            wav_path, audio_cfg = await _audio_queue.get()
            try:
                sink = audio_cfg.get("sink", "")
                volume = audio_cfg.get("volume", 1.0)
                await asyncio.to_thread(_player.play, wav_path, sink, volume)
            except Exception as e:
                logger.warning("audio playback failed: %s", e)
            finally:
                _audio_queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception:
            pass


async def _play_audio(wav_path: str, audio_cfg=None):
    """Queue audio file for sequential playback."""
    audio_cfg = audio_cfg or {}
    try:
        _audio_queue.put_nowait((wav_path, audio_cfg))
    except asyncio.QueueFull:
        logger.debug("audio queue full, skipping narration")


@app.post("/reset-history")
async def reset_history():
    """Clear the rolling session history on all narration providers."""
    if _generator:
        _generator.reset_history()
    return {"status": "history_cleared"}


@app.post("/stop")
async def stop_audio():
    """Stop currently playing audio."""
    if _player:
        _player.stop()
    return {"status": "stopped"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    uptime = time.monotonic() - _start_time
    provider_status = _generator.health_map() if _generator else {}
    piper_ok = _tts.check_available() if _tts else False
    return HealthResponse(
        status="ok",
        uptime_seconds=round(uptime, 1),
        providers=provider_status,
        provider_chain=[p.name for p in (_generator.providers if _generator else [])],
        piper_available=piper_ok,
        opencode_connected=_opencode_connected,
    )


def run():
    """Start the daemon server."""
    import uvicorn

    cfg = load_config()
    daemon_cfg = cfg.get("daemon", {})
    log_level = daemon_cfg.get("log_level", "info")

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    uvicorn.run(
        app,
        host=daemon_cfg.get("host", "127.0.0.1"),
        port=daemon_cfg.get("port", 7742),
        log_level=log_level,
    )


if __name__ == "__main__":
    run()
