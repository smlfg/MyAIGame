"""Voice integration module for MyAIGame TUI.

Provides TTS output (via Edge TTS narration daemon on port 7742),
STT input (Whisper push-to-talk), and a VoiceManager that coordinates both.

Usage:
    from tui.voice import VoiceManager, TTSClient

    manager = VoiceManager()
    await manager.start()
    await manager.speak("Research complete.")
    await manager.stop()
"""

from tui.voice.tts import TTSClient
from tui.voice.manager import VoiceManager
from tui.voice.commands import VOICE_COMMANDS, parse_voice_command

__all__ = [
    "TTSClient",
    "VoiceManager",
    "VOICE_COMMANDS",
    "parse_voice_command",
]
