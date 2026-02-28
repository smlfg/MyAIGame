"""Piper TTS wrapper with Edge-tts FIRST, then Piper, then spd-say."""

import asyncio
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger("multikanal.tts.piper")


class PiperTTS:
    """Wraps Edge TTS (first), Piper (second), spd-say (last)."""

    EDGE_VOICES = {
        "claude_code": "de-DE-FlorianMultilingualNeural",
        "claude_hook": "de-DE-FlorianMultilingualNeural",
        "claude_stop": "de-DE-FlorianMultilingualNeural",
        "opencode": "de-DE-ConradNeural",
        "opencode_live": "de-DE-ConradNeural",
        "opencode_final": "de-DE-ConradNeural",
        "codex": "de-DE-SeraphinaMultilingualNeural",
        "codex_wrapper": "de-DE-SeraphinaMultilingualNeural",
        "gemini": "de-DE-KillianNeural",
        "de": "de-DE-FlorianMultilingualNeural",
        "en": "en-US-AriaNeural",
        "en_male": "en-US-GuyNeural",
    }

    def __init__(
        self,
        command: str = "",
        voices: dict | None = None,
        default_voice: str = "de",
        speed: float = 1.0,
        voice_settings: dict | None = None,
    ):
        self._command = command or shutil.which("piper") or ""
        self._voices = voices or {}
        self.default_voice = default_voice
        self._speed = speed
        # Edge-TTS rate string: speed 1.2 → "+20%", speed 0.8 → "-20%"
        pct = int((speed - 1.0) * 100)
        self._edge_rate = f"{pct:+d}%" if pct != 0 else "+0%"
        self._voice_settings = voice_settings or {}
        self._spd_say = "/usr/bin/spd-say"
        self._edge_available = self._check_edge()

    def _check_edge(self) -> bool:
        try:
            import edge_tts

            return True
        except ImportError:
            return False

    def resolve_voice(self, key: str) -> str:
        """Resolve a voice key to Edge TTS name or Piper model path."""
        if not key:
            return self.EDGE_VOICES.get(
                self.default_voice, "de-DE-FlorianMultilingualNeural"
            )

        # Already an Edge TTS voice name
        if "Neural" in key:
            return key

        # Check EDGE_VOICES first (agent names)
        if key in self.EDGE_VOICES:
            return self.EDGE_VOICES[key]

        # Check if it's a valid Piper model path
        if key and Path(key).exists() and Path(key).stat().st_size > 10000:
            return str(Path(key))

        # Fallback to Edge
        return self.EDGE_VOICES.get(
            self.default_voice, "de-DE-FlorianMultilingualNeural"
        )

    def check_available(self) -> bool:
        return self._edge_available or Path(self._spd_say).exists()

    def synthesize(self, text: str, voice: str) -> str | None:
        if not text.strip():
            return None

        outfile = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, prefix="multikanal_"
        )
        outpath = Path(outfile.name)
        outfile.close()

        voice_name = self.resolve_voice(voice)

        # 1) Edge TTS FIRST (best quality, always works)
        if self._edge_available:
            if self._synthesize_edge(text, voice_name, str(outpath)):
                return str(outpath)

        # 2) Piper only if valid model exists
        if self._command and voice_name.endswith(".onnx") and Path(voice_name).exists():
            if self._synthesize_piper(text, voice_name, outpath):
                return str(outpath)

        # 3) spd-say last resort
        if self._synthesize_spd_say(text, voice_name, str(outpath)):
            return str(outpath)

        outpath.unlink(missing_ok=True)
        return None

    def _synthesize_edge(self, text: str, voice: str, outpath: str) -> bool:
        if not self._edge_available:
            return False

        try:
            import edge_tts

            # Per-voice rate/pitch override
            rate = self._edge_rate
            pitch = "+0Hz"
            for key, settings in self._voice_settings.items():
                if isinstance(settings, dict) and self.resolve_voice(key) == voice:
                    rate = settings.get("rate", rate)
                    pitch = settings.get("pitch", pitch)
                    break

            async def _save():
                communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                await communicate.save(outpath)

            asyncio.run(_save())
            logger.info(
                "edge-tts synthesized %d chars (rate=%s pitch=%s) -> %s",
                len(text),
                rate,
                pitch,
                outpath,
            )
            return Path(outpath).exists()

        except Exception as e:
            logger.debug("edge-tts failed: %s", e)
            return False

    def _synthesize_piper(self, text: str, voice: str, outpath: Path) -> bool:
        if not self._command:
            return False
        if not voice.endswith(".onnx") or not Path(voice).exists():
            return False

        try:
            cmd = [self._command, "--model", voice, "--output_file", str(outpath)]
            if self._speed != 1.0:
                cmd.extend(["--length_scale", str(1.0 / self._speed)])

            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
                timeout=30,
            )
            logger.info("piper synthesized %d chars -> %s", len(text), outpath)
            return True

        except Exception as e:
            logger.debug("piper failed: %s", e)
            return False

    def _synthesize_spd_say(self, text: str, voice: str, outpath: str) -> bool:
        cmd = [
            self._spd_say,
            "-w",
            outpath,
            "-r",
            str(int((self._speed - 1.0) * 100)),
            "-p",
            "50",
        ]

        if voice.startswith("de"):
            cmd.extend(["-l", "de"])
        elif voice.startswith("en"):
            cmd.extend(["-l", "en"])

        cmd.append(text)

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            logger.info("spd-say synthesized %d chars -> %s", len(text), outpath)
            return True
        except Exception as e:
            logger.debug("spd-say failed: %s", e)
            return False
