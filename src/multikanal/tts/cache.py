"""SHA-256 hash-based WAV cache with LRU eviction."""

import hashlib
import logging
import os
import pathlib
import shutil

logger = logging.getLogger("multikanal.tts.cache")


class AudioCache:
    """Caches synthesized WAV files keyed by content hash.

    Uses SHA-256(text + voice) as the cache key.
    LRU eviction based on file access time when max_entries exceeded.
    """

    def __init__(self, cache_dir: str = "~/.cache/multikanal", max_entries: int = 500):
        self._dir = pathlib.Path(os.path.expanduser(cache_dir)).resolve()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._max_entries = max_entries

    @staticmethod
    def _hash_key(text: str, voice: str) -> str:
        """Generate a cache key from text and voice."""
        h = hashlib.sha256()
        h.update(text.encode("utf-8"))
        h.update(b"|")
        h.update(voice.encode("utf-8"))
        return h.hexdigest()

    def _path_for(self, key: str) -> pathlib.Path:
        return self._dir / f"{key}.wav"

    def get(self, text: str, voice: str) -> str | None:
        """Look up a cached WAV file. Returns path string or None."""
        key = self._hash_key(text, voice)
        path = self._path_for(key)

        if path.exists():
            # Touch access time for LRU
            path.touch()
            logger.debug("cache hit: %s", key[:12])
            return str(path)

        return None

    def put(self, text: str, voice: str, wav_path: str) -> str:
        """Store a WAV file in the cache. Returns the cached path."""
        key = self._hash_key(text, voice)
        dest = self._path_for(key)

        if not dest.exists():
            shutil.copy2(wav_path, dest)
            logger.debug("cached: %s", key[:12])

        self._evict_if_needed()
        return str(dest)

    def _evict_if_needed(self):
        """Remove oldest entries if cache exceeds max size."""
        entries = list(self._dir.glob("*.wav"))
        if len(entries) <= self._max_entries:
            return

        # Sort by access time (oldest first)
        entries.sort(key=lambda p: p.stat().st_atime)

        to_remove = len(entries) - self._max_entries
        for path in entries[:to_remove]:
            try:
                path.unlink()
                logger.debug("evicted: %s", path.name)
            except OSError:
                pass

    def clear(self):
        """Remove all cached files."""
        for path in self._dir.glob("*.wav"):
            try:
                path.unlink()
            except OSError:
                pass
        logger.info("cache cleared")

    @property
    def size(self) -> int:
        """Number of cached entries."""
        return len(list(self._dir.glob("*.wav")))
