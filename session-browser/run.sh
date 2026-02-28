#!/usr/bin/env bash
# Claude Code Session Browser — Starter Script
# chmod +x run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Claude Code Session Browser ==="
echo ""

# Create venv if it doesn't exist
VENV_CREATED=false
if [ ! -d ".venv" ]; then
    echo "[1/4] Erstelle virtuelle Umgebung..."
    python3 -m venv .venv
    VENV_CREATED=true
    echo "      Fertig."
else
    echo "[1/4] Virtuelle Umgebung vorhanden."
fi

# Activate venv
echo "[2/4] Aktiviere virtuelle Umgebung..."
source .venv/bin/activate
echo "      Aktiv: $(python3 --version)"

# Install dependencies if venv was just created or requirements changed
REQUIREMENTS_STAMP=".venv/.requirements_stamp"
if [ "$VENV_CREATED" = true ] || [ ! -f "$REQUIREMENTS_STAMP" ] || [ "requirements.txt" -nt "$REQUIREMENTS_STAMP" ]; then
    echo "[3/4] Installiere Abhaengigkeiten..."
    pip install -q -r requirements.txt
    touch "$REQUIREMENTS_STAMP"
    echo "      Abhaengigkeiten installiert."
else
    echo "[3/4] Abhaengigkeiten aktuell, kein Update noetig."
fi

# Start Streamlit
echo "[4/4] Starte Session Browser auf http://localhost:8501 ..."
echo ""
echo "      Druecke Ctrl+C zum Beenden."
echo ""

streamlit run app.py --server.port 8501 --server.headless true

echo ""
echo "Tipp: alias claude-browser='~/Projekte/MyAIGame/bin/claude-browser'"
