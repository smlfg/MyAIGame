#!/usr/bin/env bash
# Download and install Piper TTS binary + voice models
set -euo pipefail

PIPER_VERSION="2023.11.14-2"
PIPER_DIR="$HOME/.local/share/piper"
PIPER_BIN="$PIPER_DIR/piper"
VOICES_DIR="$PIPER_DIR/voices"

echo "  Piper TTS Installer"

# Check if already installed
if [ -x "$PIPER_BIN" ]; then
    echo "  Piper already installed at $PIPER_BIN"
else
    # Also check system PATH
    if command -v piper &>/dev/null; then
        echo "  Piper found in PATH: $(which piper)"
        PIPER_BIN="$(which piper)"
    else
        echo "  Downloading Piper $PIPER_VERSION..."

        ARCH="$(uname -m)"
        case "$ARCH" in
            x86_64) PIPER_ARCH="amd64" ;;
            aarch64) PIPER_ARCH="arm64" ;;
            *) echo "  Unsupported architecture: $ARCH"; exit 1 ;;
        esac

        PIPER_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_${PIPER_ARCH}.tar.gz"

        mkdir -p "$PIPER_DIR"
        TMP_FILE="$(mktemp)"
        curl -fSL "$PIPER_URL" -o "$TMP_FILE"
        tar -xzf "$TMP_FILE" -C "$PIPER_DIR" --strip-components=1
        rm -f "$TMP_FILE"
        chmod +x "$PIPER_BIN"

        echo "  Installed Piper to $PIPER_BIN"

        # Add to PATH hint
        if ! echo "$PATH" | grep -q "$PIPER_DIR"; then
            echo "  NOTE: Add to your PATH:"
            echo "    export PATH=\"$PIPER_DIR:\$PATH\""
        fi
    fi
fi

# Download voice models
mkdir -p "$VOICES_DIR"

download_voice() {
    local name="$1"
    local url="$2"
    local dest="$VOICES_DIR/$name.onnx"

    if [ -f "$dest" ]; then
        echo "  Voice '$name' already downloaded"
        return
    fi

    echo "  Downloading voice: $name..."
    curl -fSL "$url" -o "$dest"
    # Also download the JSON config
    curl -fSL "${url}.json" -o "${dest}.json" 2>/dev/null || true
    echo "  Saved to $dest"
}

# German voice: thorsten-medium
download_voice "de_DE-thorsten-medium" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx"

# English voice: lessac-medium
download_voice "en_US-lessac-medium" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"

echo "  Piper setup complete"
echo "  Binary: $PIPER_BIN"
echo "  Voices: $VOICES_DIR"
