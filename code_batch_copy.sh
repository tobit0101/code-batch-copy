#!/bin/bash

# Ermittelt den absoluten Pfad des Verzeichnisses
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQ_FILE="$SCRIPT_DIR/requirements.txt"
MAIN_SCRIPT="$SCRIPT_DIR/code_batch_copy.py"

# Funktion: Finde den besten Python Interpreter
find_python() {
    # Suche spezifische Versionen bevorzugt
    candidates=("python3.12" "python3.11" "python3.10" "python3.9" "python3" "python")

    for cmd in "${candidates[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            # Prüfe ob Version >= 3.9
            ver_check=$($cmd -c 'import sys; print(1) if sys.version_info >= (3, 9) else print(0)' 2>/dev/null)
            if [ "$ver_check" == "1" ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

# 1. Den richtigen Interpreter suchen
PYTHON_CMD=$(find_python)

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ FEHLER: Kein kompatibles Python (3.9+) gefunden."
    echo "   Bitte installiere Python 3.9 oder neuer auf diesem System."
    exit 1
fi

# 2. Prüfen, ob Venv existiert und valide ist
if [ -d "$VENV_DIR" ]; then
    # Testen, ob das Python im Venv noch funktioniert
    "$VENV_DIR/bin/python" -c "import sys" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "⚠️  Bestehende virtuelle Umgebung ist defekt. Lösche und erstelle neu..."
        rm -rf "$VENV_DIR"
    fi
fi

# 3. Venv erstellen falls nicht vorhanden
if [ ! -d "$VENV_DIR" ]; then
    echo "🔨 Erstelle virtuelle Umgebung mit $PYTHON_CMD..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
fi

# 4. Dependencies installieren (Lazy Check)
"$VENV_DIR/bin/python" -c "import questionary; import pyperclip" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installiere Abhängigkeiten..."
    "$VENV_DIR/bin/pip" install --quiet --upgrade -r "$REQ_FILE"
fi

# 5. Starten
exec "$VENV_DIR/bin/python" "$MAIN_SCRIPT" "$@"
