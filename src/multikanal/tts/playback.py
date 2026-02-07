"""Audio playback with multi-tool fallback and sink/volume support."""

import logging
import os
import shutil
import subprocess

logger = logging.getLogger("multikanal.tts.playback")

# Playback tools in preference order
_PLAYBACK_TOOLS = ["paplay", "ffplay", "aplay"]


class AudioPlayer:
    """Fallback playback: paplay -> ffplay -> aplay, with optional sink/volume."""

    def __init__(self, tool: str = ""):
        self._preferred = tool
        self._process: subprocess.Popen | None = None

    def stop(self):
        """Stop currently playing audio."""
        if self._process:
            try:
                self._process.terminate()
                self._process = None
            except Exception:
                pass

    def _candidates(self, wav_path: str, sink: str, volume: float):
        env_base = os.environ.copy()
        if sink:
            env_base["PULSE_SINK"] = sink

        vol = max(0.1, min(volume, 2.0))
        paplay_vol = int(min(65536, max(3277, vol * 65536)))  # ~5%..200%
        ffplay_vol = int(min(100, max(5, vol * 100)))

        tools = []
        if self._preferred:
            tools.append(self._preferred)
        tools += _PLAYBACK_TOOLS

        seen = set()
        for tool in tools:
            if tool in seen:
                continue
            seen.add(tool)
            if shutil.which(tool):
                if tool == "paplay":
                    cmd = ["paplay"]
                    if paplay_vol and paplay_vol != 65536:
                        cmd += ["--volume", str(paplay_vol)]
                    cmd += [wav_path]
                elif tool == "ffplay":
                    cmd = [
                        "ffplay",
                        "-nodisp",
                        "-autoexit",
                        "-loglevel",
                        "quiet",
                        "-volume",
                        str(ffplay_vol),
                        wav_path,
                    ]
                else:  # aplay
                    cmd = ["aplay", wav_path]
                yield cmd, env_base

    def play(self, wav_path: str, sink: str = "", volume: float = 1.0) -> bool:
        for cmd, env in self._candidates(wav_path, sink, volume):
            tool = cmd[0]
            try:
                self._process = subprocess.Popen(
                    cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                self._process.wait()
                if self._process.returncode == 0:
                    logger.info(
                        "played audio with %s (sink=%s, vol=%.2f)",
                        tool,
                        sink or "default",
                        volume,
                    )
                    return True
            except Exception as exc:  # pragma: no cover
                logger.debug("playback failed with %s: %s", tool, exc)
                continue
        logger.warning("no playback tool succeeded")
        return False
