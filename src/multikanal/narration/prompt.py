"""Hot-reloadable prompt template loader using watchdog."""

import logging
import pathlib
import threading

logger = logging.getLogger("multikanal.narration.prompt")


class PromptWatcher:
    """Watches a prompt file and reloads it on change.

    Uses watchdog for file system monitoring. Falls back to
    manual reload if watchdog is unavailable.
    """

    def __init__(self, prompt_path: str):
        self._path = pathlib.Path(prompt_path) if prompt_path else None
        self._prompt: str = ""
        self._lock = threading.Lock()
        self._observer = None
        self._load()

    def _load(self):
        """Load the prompt file from disk."""
        if not self._path or not self._path.exists():
            logger.debug("prompt file not found: %s", self._path)
            return
        try:
            content = self._path.read_text(encoding="utf-8").strip()
            with self._lock:
                self._prompt = content
            logger.info("loaded prompt from %s (%d chars)", self._path, len(content))
        except Exception as e:
            logger.warning("failed to load prompt: %s", e)

    def get_prompt(self) -> str:
        """Get the current prompt text (thread-safe)."""
        with self._lock:
            return self._prompt

    def start(self):
        """Start watching the prompt file for changes."""
        if not self._path:
            return
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer

            watcher = self

            class _Handler(FileSystemEventHandler):
                def on_modified(self, event):
                    if pathlib.Path(event.src_path).resolve() == watcher._path.resolve():
                        logger.info("prompt file changed, reloading")
                        watcher._load()

            self._observer = Observer()
            self._observer.schedule(
                _Handler(), str(self._path.parent), recursive=False
            )
            self._observer.daemon = True
            self._observer.start()
            logger.info("watching prompt file: %s", self._path)
        except ImportError:
            logger.info("watchdog not installed, prompt hot-reload disabled")
        except Exception as e:
            logger.warning("failed to start prompt watcher: %s", e)

    def stop(self):
        """Stop the file watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None
