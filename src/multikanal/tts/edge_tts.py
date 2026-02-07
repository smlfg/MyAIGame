"""Edge TTS - Microsoft Azure Text-to-Speech (kostenlos über Edge Browser API)."""

from __future__ import annotations

import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import edge_tts


class EdgeTTS:
    """TTS using Microsoft Edge's online TTS service (free)."""

    VOICES = {
        "de": "de-DE-KatjaNeural",  # Weiblich, natürlich
        "de_male": "de-DE-ConradNeural",  # Männlich, tief
        "en": "en-US-AriaNeural",  # Weiblich, Standard
        "en_male": "en-US-GuyNeural",  # Männlich
        "fr": "fr-FR-VivienneNeural",  # Weiblich
        "es": "es-ES-ElviraNeural",  # Weiblich
    }

    def __init__(self, default_voice: str = "de", speed: float = 1.0):
        self.default_voice = self.VOICES.get(default_voice, default_voice)
        self.speed = speed

    async def _synthesize_async(self, text: str, voice: str) -> Path:
        """Async synthesis using edge-tts."""
        voice_name = self.VOICES.get(voice, voice)

        communicate = edge_tts.Communicate(text, voice_name)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = Path(tmp.name)

        await communicate.save(str(output_path))
        return output_path

    def synthesize(self, text: str, voice: str = "de") -> Path | None:
        """Synthesize text to speech."""
        if not text.strip():
            return None

        try:
            return asyncio.run(self._synthesize_async(text, voice))
        except Exception as e:
            print(f"Edge TTS Error: {e}")
            return None

    @staticmethod
    def is_available() -> bool:
        """Check if edge-tts is installed."""
        try:
            import edge_tts

            return True
        except ImportError:
            return False


if __name__ == "__main__":
    import sys

    tts = EdgeTTS()

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "Hallo Welt, ich bin BipBub!"

    print(f"Test: {text}")
    path = tts.synthesize(text, "de")
    if path:
        print(f"Audio: {path}")
        subprocess.run(["aplay", str(path)], check=False)
