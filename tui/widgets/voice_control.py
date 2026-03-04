"""VoiceControlWidget — voice status + toggle."""
import subprocess
import urllib.request
import urllib.error
from textual.widgets import Static


VOICE_PORT = 5050
VOICE_URL = f"http://127.0.0.1:{VOICE_PORT}"
VOICE_SERVICE = "voicemode-edge-tts"


def _check_voice_health() -> bool:
    """Return True if voice service is reachable."""
    try:
        req = urllib.request.urlopen(VOICE_URL, timeout=2)
        return req.status < 500
    except Exception:
        return False


class VoiceControlWidget(Static):
    """Shows voice status and provides toggle control."""

    DEFAULT_CSS = """
    VoiceControlWidget {
        background: #161b22;
        color: #e6edf3;
        border: solid #30363d;
        height: auto;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self._online = False

    def on_mount(self) -> None:
        self._check_and_render()
        self.set_interval(10, self._check_and_render)

    def _check_and_render(self) -> None:
        self.run_worker(self._async_check, exclusive=True)

    async def _async_check(self) -> None:
        import asyncio
        self._online = await asyncio.to_thread(_check_voice_health)
        self._render()

    def _render(self) -> None:
        if self._online:
            status = f"[bold #3fb950]ON[/bold #3fb950] Port {VOICE_PORT}"
            action = "[dim]Press T to stop[/dim]"
        else:
            status = "[bold #f85149]OFF[/bold #f85149]"
            action = "[dim]Press T to start[/dim]"
        self.update(f"[bold]Voice[/bold]\n{status}\n{action}")

    def on_key(self, event) -> None:
        if event.key == "t":
            self._toggle_voice()

    def _toggle_voice(self) -> None:
        action = "stop" if self._online else "start"
        try:
            subprocess.run(
                ["systemctl", "--user", action, VOICE_SERVICE],
                timeout=5,
                capture_output=True,
            )
        except Exception:
            pass
        self._check_and_render()
