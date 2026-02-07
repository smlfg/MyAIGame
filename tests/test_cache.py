"""Tests for TTS audio cache."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from multikanal.tts.cache import AudioCache


def _make_cache(max_entries=10):
    tmpdir = tempfile.mkdtemp(prefix="multikanal_test_cache_")
    return AudioCache(cache_dir=tmpdir, max_entries=max_entries), tmpdir


def _make_wav(content="fake wav data"):
    f = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    f.write(content.encode())
    f.close()
    return f.name


def test_cache_miss():
    cache, _ = _make_cache()
    assert cache.get("hello world", "de") is None


def test_cache_put_and_get():
    cache, _ = _make_cache()
    wav = _make_wav()
    cache.put("hello world", "de", wav)
    result = cache.get("hello world", "de")
    assert result is not None
    assert result.endswith(".wav")
    os.unlink(wav)


def test_cache_different_voice():
    cache, _ = _make_cache()
    wav = _make_wav()
    cache.put("hello world", "de", wav)
    assert cache.get("hello world", "de") is not None
    assert cache.get("hello world", "en") is None
    os.unlink(wav)


def test_cache_different_text():
    cache, _ = _make_cache()
    wav = _make_wav()
    cache.put("hello", "de", wav)
    assert cache.get("hello", "de") is not None
    assert cache.get("world", "de") is None
    os.unlink(wav)


def test_cache_size():
    cache, _ = _make_cache()
    assert cache.size == 0
    wav = _make_wav()
    cache.put("test", "de", wav)
    assert cache.size == 1
    os.unlink(wav)


def test_cache_clear():
    cache, _ = _make_cache()
    wav = _make_wav()
    cache.put("test1", "de", wav)
    cache.put("test2", "de", wav)
    assert cache.size == 2
    cache.clear()
    assert cache.size == 0
    os.unlink(wav)


def test_cache_eviction():
    cache, _ = _make_cache(max_entries=3)
    wav = _make_wav()
    for i in range(5):
        cache.put(f"text_{i}", "de", wav)
    assert cache.size <= 3
    os.unlink(wav)


def test_hash_deterministic():
    """Same text+voice always produces same hash."""
    h1 = AudioCache._hash_key("hello", "de")
    h2 = AudioCache._hash_key("hello", "de")
    assert h1 == h2


def test_hash_different_inputs():
    h1 = AudioCache._hash_key("hello", "de")
    h2 = AudioCache._hash_key("hello", "en")
    h3 = AudioCache._hash_key("world", "de")
    assert h1 != h2
    assert h1 != h3
