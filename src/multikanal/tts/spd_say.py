"""Simple TTS wrapper using spd-say (Speech Dispatcher)."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SpdSayTTS:
    """TTS using speech-dispatcher's spd-say."""

    def __init__(
        self,
        voice: str = "de",
        speed: float = 1.0,
        pitch: int = 50,
    ):
        """Initialize spd-say TTS.

        Args:
            voice: Language code (de, en, etc.)
            speed: Speech rate (0.5 to 2.0)
            pitch: Pitch adjustment (0 to 100)
        """
        self.voice = voice
        self.speed = speed
        self.pitch = pitch
        self.command = "/usr/bin/spd-say"

        self._verify_installation()

    def _verify_installation(self) -> None:
        """Verify spd-say is available."""
        try:
            result = subprocess.run(
                [self.command, "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError("spd-say returned non-zero exit code")
        except FileNotFoundError:
            raise RuntimeError("spd-say not found in PATH")

    def synthesize(self, text: str) -> Path:
        """Synthesize text to speech.

        Args:
            text: Text to speak

        Returns:
            Path to WAV file (temp file)
        """
        if not text.strip():
            raise ValueError("Cannot synthesize empty text")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            output_path = Path(tmp.name)

        cmd = [
            self.command,
            "-w",
            str(output_path),
            "-r",
            str(int((self.speed - 1.0) * 100)),
            "-p",
            str(self.pitch),
        ]

        if self.voice.startswith("de"):
            cmd.extend(["-l", "de"])
        elif self.voice.startswith("en"):
            cmd.extend(["-l", "en"])

        cmd.append(text)

        logger.debug(f"Running: {' '.join(cmd[:3])}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.error(f"spd-say failed: {result.stderr}")
            output_path.unlink(missing_ok=True)
            raise RuntimeError(f"spd-say failed: {result.stderr}")

        if not output_path.exists():
            raise RuntimeError(f"spd-say did not produce output: {output_path}")

        return output_path

    def speak(self, text: str, blocking: bool = True) -> None:
        """Speak text directly without saving to file.

        Args:
            text: Text to speak
            blocking: Wait for speech to complete
        """
        if not text.strip():
            return

        cmd = [
            self.command,
            "-e",
            "-r",
            str(int((self.speed - 1.0) * 100)),
            "-p",
            str(self.pitch),
        ]

        if self.voice.startswith("de"):
            cmd.extend(["-l", "de"])
        elif self.voice.startswith("en"):
            cmd.extend(["-l", "en"])

        cmd.append(text)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if blocking:
                proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()

    @staticmethod
    def is_available() -> bool:
        """Check if spd-say is available."""
        return Path("/usr/bin/spd-say").exists()
