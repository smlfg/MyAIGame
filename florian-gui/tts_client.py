#!/usr/bin/env python3
"""Non-blocking HTTP client for Edge TTS server.

Uses GLib.spawn_async with curl for non-blocking HTTP — no threading.
"""

import json
import os
import tempfile

from gi.repository import GLib

SERVER_URL = "http://localhost:5050"


def _cleanup_tmp(path: str) -> None:
    """Remove a temp file, ignoring errors."""
    try:
        os.unlink(path)
    except OSError:
        pass


def health_check(callback, error_callback=None) -> None:
    """Check server health asynchronously."""
    _curl_get(f"{SERVER_URL}/health", callback, error_callback)


def get_voices(callback, error_callback=None) -> None:
    """Fetch available voices asynchronously."""
    _curl_get(f"{SERVER_URL}/v1/audio/voices", callback, error_callback)


def synthesize(text: str, voice: str, speed: float, response_format: str,
               callback, error_callback=None) -> None:
    """Send TTS request and save audio to temp file.

    callback receives the path to the temp audio file.
    """
    body = json.dumps({
        "input": text,
        "voice": voice,
        "speed": speed,
        "response_format": response_format,
    })

    suffix = f".{response_format}" if response_format else ".mp3"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, prefix="florian-tts-")
    tmp_path = tmp.name
    tmp.close()

    cmd = [
        "curl", "-s", "-X", "POST",
        f"{SERVER_URL}/v1/audio/speech",
        "-H", "Content-Type: application/json",
        "-d", body,
        "-o", tmp_path,
        "--max-time", "30",
        "-w", "%{http_code}",
    ]

    def _on_done(pid, status):
        if os.waitstatus_to_exitcode(status) != 0:
            _cleanup_tmp(tmp_path)
            if error_callback:
                GLib.idle_add(error_callback, "curl failed")
            return

        # Check if file has data
        try:
            size = os.path.getsize(tmp_path)
            if size > 100:  # audio files are always > 100 bytes
                GLib.idle_add(callback, tmp_path)
            elif error_callback:
                # Read the error body
                try:
                    with open(tmp_path, "rb") as f:
                        err = f.read().decode(errors="replace")
                    GLib.idle_add(error_callback, f"Server error: {err[:200]}")
                except Exception:
                    GLib.idle_add(error_callback, "Empty response from server")
                _cleanup_tmp(tmp_path)
        except OSError as e:
            _cleanup_tmp(tmp_path)
            if error_callback:
                GLib.idle_add(error_callback, str(e))

    try:
        pid, stdin_fd, stdout_fd, stderr_fd = GLib.spawn_async(
            cmd,
            flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD | GLib.SpawnFlags.SEARCH_PATH,
        )
        GLib.child_watch_add(pid, _on_done)
    except GLib.Error as e:
        if error_callback:
            error_callback(f"Failed to start curl: {e.message}")


def _curl_get(url: str, callback, error_callback=None) -> None:
    """Async GET request via curl + GLib.spawn_async."""
    cmd = ["curl", "-s", "--max-time", "5", url]

    def _on_done(pid, status, stdout_data):
        if os.waitstatus_to_exitcode(status) != 0:
            if error_callback:
                GLib.idle_add(error_callback, "Connection failed")
            return
        try:
            data = json.loads(stdout_data)
            GLib.idle_add(callback, data)
        except (json.JSONDecodeError, TypeError) as e:
            if error_callback:
                GLib.idle_add(error_callback, str(e))

    try:
        result, pid, stdin_fd, stdout_fd, stderr_fd = GLib.spawn_async_with_pipes(
            None, cmd, None,
            GLib.SpawnFlags.DO_NOT_REAP_CHILD | GLib.SpawnFlags.SEARCH_PATH,
            None, None,
        )

        # Read stdout via io_add_watch
        chunks = []

        def _on_read(fd, condition):
            if condition & GLib.IO_IN:
                data = os.read(fd, 65536)
                if data:
                    chunks.append(data)
                    return True
            # EOF or error
            os.close(fd)
            stdout_data = b"".join(chunks).decode()
            # Wait for child
            GLib.child_watch_add(pid, lambda p, s: _on_done(p, s, stdout_data))
            return False

        GLib.io_add_watch(stdout_fd, GLib.IO_IN | GLib.IO_HUP, _on_read)

    except GLib.Error as e:
        if error_callback:
            error_callback(f"Failed to start curl: {e.message}")
