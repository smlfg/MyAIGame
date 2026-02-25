#!/usr/bin/env python3
"""Edge TTS → OpenAI-compatible API wrapper for VoiceMode.

Exposes POST /v1/audio/speech and GET /v1/audio/voices so VoiceMode
can use Edge TTS as a drop-in TTS provider.

Usage:
    python server.py [--port 5050] [--host 127.0.0.1]
    # or via systemd: voicemode-edge-tts.service
"""

from __future__ import annotations

import argparse
import asyncio
import io
import logging
import subprocess
import tempfile
from pathlib import Path

import edge_tts
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

logger = logging.getLogger("edge-tts-server")

# ---------------------------------------------------------------------------
# Voice mapping: OpenAI-style names → Edge TTS voices
# ---------------------------------------------------------------------------

VOICE_MAP: dict[str, str] = {
    # German voices (primary for Samuel)
    "florian": "de-DE-FlorianMultilingualNeural",
    "katja": "de-DE-KatjaNeural",
    "conrad": "de-DE-ConradNeural",
    "amala": "de-DE-AmalaNeural",
    "killian": "de-DE-KillianNeural",
    "seraphina": "de-DE-SeraphinaMultilingualNeural",
    # English voices
    "aria": "en-US-AriaNeural",
    "guy": "en-US-GuyNeural",
    "jenny": "en-US-JennyNeural",
    "davis": "en-US-DavisNeural",
    # OpenAI-compatible aliases → German defaults
    "alloy": "de-DE-FlorianMultilingualNeural",
    "echo": "de-DE-ConradNeural",
    "fable": "de-DE-KillianNeural",
    "onyx": "de-DE-ConradNeural",
    "nova": "de-DE-KatjaNeural",
    "shimmer": "de-DE-AmalaNeural",
    # Kokoro-style aliases
    "af_sky": "de-DE-KatjaNeural",
    "af_sarah": "de-DE-AmalaNeural",
    "am_adam": "de-DE-ConradNeural",
}

DEFAULT_VOICE = "de-DE-FlorianMultilingualNeural"
DEFAULT_RATE = "-5%"
DEFAULT_PITCH = "+0Hz"

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Edge TTS OpenAI-Compatible Server", version="1.0.0")


class SpeechRequest(BaseModel):
    model: str = "tts-1"
    input: str
    voice: str = "alloy"
    response_format: str = "mp3"
    speed: float = 1.0


def resolve_voice(voice: str) -> str:
    """Resolve a voice name to an Edge TTS voice identifier."""
    # Direct Edge TTS voice name (e.g. de-DE-FlorianMultilingualNeural)
    if "-" in voice and "Neural" in voice:
        return voice
    return VOICE_MAP.get(voice.lower(), DEFAULT_VOICE)


def speed_to_rate(speed: float) -> str:
    """Convert OpenAI speed (0.25-4.0, 1.0=normal) to Edge TTS rate string."""
    pct = int(round((speed - 1.0) * 100))
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"


async def synthesize(text: str, voice: str, rate: str, pitch: str) -> bytes:
    """Synthesize text to MP3 bytes using edge-tts."""
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    audio_chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
    if not audio_chunks:
        raise RuntimeError("Edge TTS returned no audio data")
    return b"".join(audio_chunks)


def convert_format(mp3_bytes: bytes, target_format: str) -> tuple[bytes, str]:
    """Convert MP3 bytes to the requested format. Returns (data, content_type)."""
    format_map = {
        "mp3": ("audio/mpeg", None),
        "opus": ("audio/opus", ["opus"]),
        "aac": ("audio/aac", ["adts"]),
        "flac": ("audio/flac", ["flac"]),
        "wav": ("audio/wav", ["wav"]),
        "pcm": ("audio/pcm", ["s16le"]),
    }
    content_type, ffmpeg_fmt = format_map.get(target_format, ("audio/mpeg", None))

    if ffmpeg_fmt is None:
        # MP3 requested or unknown → return as-is
        return mp3_bytes, content_type

    # Convert via ffmpeg
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", "pipe:0",
        "-f", ffmpeg_fmt[0],
    ]
    if target_format == "pcm":
        cmd.extend(["-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le"])
    cmd.append("pipe:1")

    try:
        result = subprocess.run(
            cmd, input=mp3_bytes, capture_output=True, timeout=15
        )
        if result.returncode != 0:
            logger.warning("ffmpeg conversion failed: %s", result.stderr.decode())
            return mp3_bytes, "audio/mpeg"
        return result.stdout, content_type
    except Exception as exc:
        logger.warning("ffmpeg error: %s — returning MP3", exc)
        return mp3_bytes, "audio/mpeg"


@app.post("/v1/audio/speech")
async def speech(req: SpeechRequest):
    """OpenAI-compatible TTS endpoint."""
    if not req.input.strip():
        raise HTTPException(status_code=400, detail="input text is empty")

    voice = resolve_voice(req.voice)
    rate = speed_to_rate(req.speed)

    logger.info(
        "TTS request: voice=%s (→%s), format=%s, speed=%s, len=%d",
        req.voice, voice, req.response_format, req.speed, len(req.input),
    )

    try:
        mp3_bytes = await synthesize(req.input, voice, rate, DEFAULT_PITCH)
    except Exception as exc:
        logger.error("Edge TTS synthesis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Edge TTS error: {exc}")

    data, content_type = convert_format(mp3_bytes, req.response_format)

    return Response(content=data, media_type=content_type)


@app.get("/v1/audio/voices")
async def list_voices():
    """Return available voices in OpenAI-compatible format."""
    voices = [{"id": name, "name": edge_voice} for name, edge_voice in VOICE_MAP.items()]
    # Also add raw Edge TTS German voices
    german_voices = [
        "de-DE-FlorianMultilingualNeural",
        "de-DE-KatjaNeural",
        "de-DE-ConradNeural",
        "de-DE-AmalaNeural",
        "de-DE-KillianNeural",
        "de-DE-SeraphinaMultilingualNeural",
    ]
    for v in german_voices:
        voices.append({"id": v, "name": v})
    return {"voices": voices}


@app.get("/v1/models")
async def list_models():
    """Return supported models (for provider discovery)."""
    return {
        "data": [
            {"id": "tts-1", "object": "model", "owned_by": "edge-tts"},
            {"id": "tts-1-hd", "object": "model", "owned_by": "edge-tts"},
        ]
    }


@app.get("/health")
async def health():
    return {"status": "ok", "provider": "edge-tts", "version": edge_tts.__version__}


def main():
    parser = argparse.ArgumentParser(description="Edge TTS OpenAI-compatible server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
