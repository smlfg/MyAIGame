#!/usr/bin/env python3
"""Audio player using mpv via GLib.spawn_async — no threading."""

import os
import shutil
import sys

from gi.repository import GLib

_PLAYER_CMD = None


def _find_player() -> list[str] | None:
    """Find available audio player: mpv preferred, paplay as fallback."""
    if shutil.which("mpv"):
        return ["mpv", "--no-video", "--no-terminal"]
    if shutil.which("paplay"):
        return ["paplay"]
    return None


class AudioPlayer:
    """Play audio files via mpv/paplay subprocess."""

    def __init__(self):
        global _PLAYER_CMD
        self._pid: int | None = None
        self._on_finished = None
        self._current_file: str | None = None
        if _PLAYER_CMD is None:
            _PLAYER_CMD = _find_player()
            if _PLAYER_CMD is None:
                print("WARNING: No audio player found (mpv or paplay)", file=sys.stderr)

    @property
    def is_playing(self) -> bool:
        return self._pid is not None

    def play(self, filepath: str, on_finished=None) -> None:
        """Play an audio file. Stops any current playback first."""
        self.stop()
        self._on_finished = on_finished
        self._current_file = filepath

        if _PLAYER_CMD is None:
            print("ERROR: No audio player available", file=sys.stderr)
            self._cleanup_file()
            if on_finished:
                GLib.idle_add(on_finished)
            return

        cmd = _PLAYER_CMD + [filepath]

        try:
            pid, _, _, _ = GLib.spawn_async(
                cmd,
                flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD | GLib.SpawnFlags.SEARCH_PATH,
            )
            self._pid = pid
            GLib.child_watch_add(pid, self._on_child_exit)
        except GLib.Error as e:
            print(f"ERROR: Failed to start audio player: {e.message}", file=sys.stderr)
            self._pid = None
            self._cleanup_file()
            if on_finished:
                GLib.idle_add(on_finished)

    def stop(self) -> None:
        """Stop current playback."""
        if self._pid is not None:
            try:
                os.kill(self._pid, 15)  # SIGTERM
            except (ProcessLookupError, PermissionError):
                pass
            self._pid = None

    def _cleanup_file(self) -> None:
        """Remove temp audio file after playback."""
        if self._current_file:
            try:
                os.unlink(self._current_file)
            except OSError:
                pass
            self._current_file = None

    def _on_child_exit(self, pid, status):
        self._pid = None
        self._cleanup_file()
        if self._on_finished:
            GLib.idle_add(self._on_finished)
            self._on_finished = None
