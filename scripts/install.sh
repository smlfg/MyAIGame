#!/usr/bin/env bash
# MultiKanalAgent — Full Installation Script
# Sets up Python venv, installs deps, downloads Piper + voices
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"

echo "=== MultiKanalAgent Installer ==="
echo "Project: $PROJECT_DIR"
echo ""

# Step 1: Python virtual environment
echo "[1/4] Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "  Created venv at $VENV_DIR"
else
    echo "  Venv already exists"
fi

source "$VENV_DIR/bin/activate"

# Step 2: Install Python dependencies
echo "[2/4] Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -e "$PROJECT_DIR"
pip install --quiet -e "$PROJECT_DIR[dev]"
echo "  Done"

# Step 3: Install Piper TTS
echo "[3/4] Installing Piper TTS..."
bash "$SCRIPT_DIR/install-piper.sh"

# Step 4: Check Ollama
echo "[4/4] Checking Ollama..."
if command -v ollama &>/dev/null; then
    echo "  Ollama found: $(ollama --version 2>/dev/null || echo 'installed')"
    # Try to pull the default model
    if ollama list 2>/dev/null | grep -q "llama3.1:8b"; then
        echo "  Model llama3.1:8b already available"
    else
        echo "  Pulling llama3.1:8b (this may take a while)..."
        ollama pull llama3.1:8b || echo "  Warning: Could not pull model. Run 'ollama pull llama3.1:8b' manually."
    fi
else
    echo "  WARNING: Ollama not found."
    echo "  Install from: https://ollama.ai"
    echo "  Then run: ollama pull llama3.1:8b"
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Quick start:"
echo "  source $VENV_DIR/bin/activate"
echo "  multikanal daemon                    # Start the daemon"
echo "  multikanal health                    # Check status"
echo "  multikanal narrate 'Hello world'     # Test narration"
echo ""
echo "Install Claude Code hooks:"
echo "  multikanal install-hooks"
