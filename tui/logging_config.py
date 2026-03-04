"""Logging configuration for MyAIGame TUI.

Sets up:
- File logging to ~/.local/share/myaigame-tui/logs/
- Rich console handler for debug mode
- Per-module loggers via getLogger(__name__)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


LOG_DIR = Path.home() / ".local" / "share" / "myaigame-tui" / "logs"
LOG_FILE = LOG_DIR / "myaigame-tui.log"

_configured = False


def setup_logging(debug: bool = False) -> None:
    """Configure logging. Call once at startup.

    Args:
        debug: If True, attach a Rich console handler at DEBUG level.
               File logging is always enabled at INFO level.
    """
    global _configured
    if _configured:
        return
    _configured = True

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("tui")
    root.setLevel(logging.DEBUG)

    # File handler — always on, INFO+ level, rotating-friendly plain format
    file_fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_fmt)
    root.addHandler(file_handler)

    # Console handler — only in debug mode
    if debug:
        try:
            from rich.logging import RichHandler

            console_handler = RichHandler(
                level=logging.DEBUG,
                show_time=True,
                show_path=True,
                markup=True,
            )
            root.addHandler(console_handler)
        except ImportError:
            # Rich not available — fall back to a plain stderr handler
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.DEBUG)
            stderr_handler.setFormatter(file_fmt)
            root.addHandler(stderr_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'tui' namespace.

    Usage:
        log = get_logger(__name__)
        log.info("Provider started")
    """
    # Ensure the name is relative to the 'tui' root logger
    if not name.startswith("tui"):
        name = f"tui.{name}"
    return logging.getLogger(name)
