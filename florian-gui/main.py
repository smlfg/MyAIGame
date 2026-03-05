#!/usr/bin/env python3
"""Florian TTS Control Panel — GTK3 standalone GUI.

Voice selection, speed/pitch controls, text input, audio playback.
Data source: Edge TTS server at localhost:5050 (FastAPI).
"""

import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

# Import shared base
sys.path.insert(0, str(Path.home() / "Projekte" / "shared-gui"))
from gui_base import BaseApp

sys.path.insert(0, str(Path.home() / "Projekte" / "ClaudeCodePanel"))
from theme import get_palette

from tts_client import health_check, get_voices, synthesize
from audio_player import AudioPlayer


class FlorianApp(BaseApp):
    """TTS Control Panel with voice selection, speed, text input, playback."""

    def __init__(self):
        super().__init__("Florian TTS Control", 600, 500, icon_name="audio-speakers")

        self._player = AudioPlayer()
        self._voices: list[dict] = []
        self._current_audio: str | None = None

        self._build_ui()

        # Load voices + health check
        GLib.idle_add(self._initial_load)

        # Health check every 10s
        self.start_refresh(10, self._check_health)

    def _build_ui(self):
        p = get_palette()

        # Play button in header
        self._play_btn = Gtk.Button(label="Speak")
        self._play_btn.get_style_context().add_class("base-accent-btn")
        self._play_btn.connect("clicked", self._on_speak)
        self.add_header_widget(self._play_btn)

        # --- Voice selection ---
        voice_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        voice_lbl = Gtk.Label(label="Voice:")
        voice_lbl.set_width_chars(8)
        voice_lbl.set_xalign(0)
        voice_box.pack_start(voice_lbl, False, False, 0)

        self._voice_combo = Gtk.ComboBoxText()
        self._voice_combo.append("florian", "Florian (de-DE)")
        self._voice_combo.set_active(0)
        voice_box.pack_start(self._voice_combo, True, True, 0)

        self.content_box.pack_start(voice_box, False, False, 0)

        # --- Speed slider ---
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        speed_lbl = Gtk.Label(label="Speed:")
        speed_lbl.set_width_chars(8)
        speed_lbl.set_xalign(0)
        speed_box.pack_start(speed_lbl, False, False, 0)

        self._speed_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0.25, 4.0, 0.25
        )
        self._speed_scale.set_value(1.0)
        self._speed_scale.set_draw_value(True)
        self._speed_scale.set_value_pos(Gtk.PositionType.RIGHT)
        speed_box.pack_start(self._speed_scale, True, True, 0)

        self.content_box.pack_start(speed_box, False, False, 0)

        # --- Format selection ---
        fmt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        fmt_lbl = Gtk.Label(label="Format:")
        fmt_lbl.set_width_chars(8)
        fmt_lbl.set_xalign(0)
        fmt_box.pack_start(fmt_lbl, False, False, 0)

        self._format_buttons: dict[str, Gtk.RadioButton] = {}
        first_btn = None
        for fmt in ("mp3", "wav", "opus", "flac"):
            if first_btn is None:
                btn = Gtk.RadioButton.new_with_label(None, fmt)
                first_btn = btn
            else:
                btn = Gtk.RadioButton.new_with_label_from_widget(first_btn, fmt)
            self._format_buttons[fmt] = btn
            fmt_box.pack_start(btn, False, False, 0)

        self.content_box.pack_start(fmt_box, False, False, 0)

        # --- Text input ---
        text_lbl = Gtk.Label(label="Text:")
        text_lbl.set_halign(Gtk.Align.START)
        text_lbl.get_style_context().add_class("section-title")
        self.content_box.pack_start(text_lbl, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(120)
        scrolled.set_vexpand(True)

        self._text_view = Gtk.TextView()
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self._text_view.get_buffer().set_text(
            "Guten Tag, ich bin Florian und teste die Sprachausgabe."
        )
        scrolled.add(self._text_view)
        self.content_box.pack_start(scrolled, True, True, 0)

        # --- Buttons row ---
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self._speak_btn = Gtk.Button(label="Speak")
        self._speak_btn.get_style_context().add_class("base-accent-btn")
        self._speak_btn.connect("clicked", self._on_speak)
        btn_box.pack_start(self._speak_btn, False, False, 0)

        self._stop_btn = Gtk.Button(label="Stop")
        self._stop_btn.get_style_context().add_class("shortcut-btn")
        self._stop_btn.set_sensitive(False)
        self._stop_btn.connect("clicked", self._on_stop)
        btn_box.pack_start(self._stop_btn, False, False, 0)

        # Spinner for loading state
        self._spinner = Gtk.Spinner()
        btn_box.pack_start(self._spinner, False, False, 0)

        self.content_box.pack_start(btn_box, False, False, 0)

        # --- Health indicator ---
        health_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        health_box.get_style_context().add_class("base-card")
        health_lbl = Gtk.Label(label="Server:")
        health_lbl.set_markup(f'<span foreground="{p["overlay"]}">Server: localhost:5050</span>')
        health_box.pack_start(health_lbl, False, False, 0)

        self._health_dot = Gtk.Label()
        self._health_dot.set_markup(f'<span foreground="{p["dim"]}">●</span>')
        health_box.pack_end(self._health_dot, False, False, 0)

        self._health_text = Gtk.Label(label="Checking...")
        self._health_text.set_markup(f'<span foreground="{p["dim"]}">Checking...</span>')
        health_box.pack_end(self._health_text, False, False, 0)

        self.content_box.pack_start(health_box, False, False, 0)

    def _initial_load(self) -> bool:
        """Load voices and check health on startup."""
        self._check_health()
        get_voices(self._on_voices_loaded, lambda e: None)
        return False  # one-shot

    def _check_health(self) -> bool:
        """Periodic health check."""
        p = get_palette()

        def _on_ok(data):
            status = data.get("status", "unknown")
            version = data.get("version", "?")
            self._health_dot.set_markup(f'<span foreground="{p["green"]}">●</span>')
            self._health_text.set_markup(
                f'<span foreground="{p["green"]}">OK (edge-tts {version})</span>'
            )
            self.set_status(f"Ready -- Florian (de-DE)", "status-saved")

        def _on_err(msg):
            self._health_dot.set_markup(f'<span foreground="{p["red"]}">●</span>')
            self._health_text.set_markup(f'<span foreground="{p["red"]}">Offline</span>')
            self.set_status("Server not reachable", "status-error")

        health_check(_on_ok, _on_err)
        return True  # keep timer

    def _on_voices_loaded(self, data):
        """Populate voice combo from server response."""
        voices = data.get("voices", [])
        self._voices = voices

        self._voice_combo.remove_all()
        seen = set()
        for v in voices:
            vid = v.get("id", "")
            name = v.get("name", vid)
            if vid not in seen:
                self._voice_combo.append(vid, f"{vid} ({name})")
                seen.add(vid)

        # Select florian by default
        self._voice_combo.set_active_id("florian")

    def _get_selected_format(self) -> str:
        for fmt, btn in self._format_buttons.items():
            if btn.get_active():
                return fmt
        return "mp3"

    def _on_speak(self, _btn):
        """Synthesize and play."""
        buf = self._text_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False).strip()
        if not text:
            self.set_status("No text to speak", "status-error")
            return

        voice = self._voice_combo.get_active_id() or "florian"
        speed = self._speed_scale.get_value()
        fmt = self._get_selected_format()

        self._speak_btn.set_sensitive(False)
        self._spinner.start()
        self.set_status("Synthesizing...")

        def _on_audio(filepath):
            self._spinner.stop()
            self._speak_btn.set_sensitive(True)
            self._stop_btn.set_sensitive(True)
            self._current_audio = filepath
            self.set_status("Playing...")
            self._player.play(filepath, on_finished=self._on_playback_done)

        def _on_err(msg):
            self._spinner.stop()
            self._speak_btn.set_sensitive(True)
            self.set_status(f"Error: {msg}", "status-error")

        synthesize(text, voice, speed, fmt, _on_audio, _on_err)

    def _on_stop(self, _btn):
        self._player.stop()
        self._stop_btn.set_sensitive(False)
        self.set_status("Stopped")

    def _on_playback_done(self):
        self._stop_btn.set_sensitive(False)
        self.set_status("Ready -- Florian (de-DE)", "status-saved")


def main():
    app = FlorianApp()
    app.run()


if __name__ == "__main__":
    main()
