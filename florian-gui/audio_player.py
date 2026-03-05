#!/usr/bin/env python3
"""Audio player using mpv via GLib.spawn_async — no threading."""

import os

from gi.repository import GLib


class AudioPlayer:
    """Play audio files via mpv subprocess."""

    def __init__(self):
        self._pid: int | None = None
        self._on_finished = None

    @property
    def is_playing(self) -> bool:
        return self._pid is not None

    def play(self, filepath: str, on_finished=None) -> None:
        """Play an audio file. Stops any current playback first."""
        self.stop()
        self._on_finished = on_finished

        cmd = ["mpv", "--no-video", "--no-terminal", filepath]

        try:
            pid, _, _, _ = GLib.spawn_async(
                cmd,
                flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD | GLib.SpawnFlags.SEARCH_PATH,
            )
            self._pid = pid
            GLib.child_watch_add(pid, self._on_child_exit)
        except GLib.Error:
            self._pid = None
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

    def _on_child_exit(self, pid, status):
        self._pid = None
        if self._on_finished:
            GLib.idle_add(self._on_finished)
            self._on_finished = None
