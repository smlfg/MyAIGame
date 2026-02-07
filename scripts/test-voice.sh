#!/usr/bin/env bash
# Quick end-to-end TTS test
# Tests Piper synthesis + playback for both German and English
set -euo pipefail

PIPER_DIR="$HOME/.local/share/piper"
PIPER_BIN="${PIPER_CMD:-$(command -v piper 2>/dev/null || echo "$PIPER_DIR/piper")}"
VOICES_DIR="$PIPER_DIR/voices"

echo "=== MultiKanalAgent Voice Test ==="
echo "Piper: $PIPER_BIN"
echo ""

if [ ! -x "$PIPER_BIN" ]; then
    echo "ERROR: Piper not found at $PIPER_BIN"
    echo "Run: bash scripts/install-piper.sh"
    exit 1
fi

# Detect playback tool
PLAY_CMD=""
for tool in paplay aplay ffplay; do
    if command -v "$tool" &>/dev/null; then
        PLAY_CMD="$tool"
        break
    fi
done

if [ -z "$PLAY_CMD" ]; then
    echo "WARNING: No playback tool found. WAV files will be created but not played."
fi

test_voice() {
    local lang="$1"
    local voice="$2"
    local text="$3"
    local model="$VOICES_DIR/$voice.onnx"

    echo "--- Testing $lang ($voice) ---"

    if [ ! -f "$model" ]; then
        echo "  SKIP: Voice model not found: $model"
        return
    fi

    local tmpfile
    tmpfile="$(mktemp --suffix=.wav)"

    echo "  Text: '$text'"
    echo "$text" | "$PIPER_BIN" --model "$model" --output_file "$tmpfile" 2>/dev/null

    if [ -f "$tmpfile" ] && [ -s "$tmpfile" ]; then
        local size
        size=$(stat -c%s "$tmpfile" 2>/dev/null || stat -f%z "$tmpfile" 2>/dev/null)
        echo "  WAV: $tmpfile ($size bytes)"

        if [ -n "$PLAY_CMD" ]; then
            echo "  Playing..."
            if [ "$PLAY_CMD" = "ffplay" ]; then
                "$PLAY_CMD" -nodisp -autoexit "$tmpfile" 2>/dev/null
            else
                "$PLAY_CMD" "$tmpfile" 2>/dev/null
            fi
            echo "  OK"
        fi
    else
        echo "  FAIL: No audio generated"
    fi

    rm -f "$tmpfile"
    echo ""
}

# Test German
test_voice "Deutsch" "de_DE-thorsten-medium" \
    "Der Agent hat gerade eine neue Datei erstellt. Sie enthält eine Konfiguration für das Projekt."

# Test English
test_voice "English" "en_US-lessac-medium" \
    "The agent just created a new configuration file for the project. It contains the default settings."

echo "=== Voice test complete ==="
