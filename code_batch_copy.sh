#!/bin/bash

# Ermittelt den absoluten Pfad des Verzeichnisses, in dem dieses Skript liegt.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Erstelle ggf. eine virtuelle Umgebung im Skript-Verzeichnis (nicht im aktuellen Arbeitsverzeichnis).
if [ ! -d "$SCRIPT_DIR/venv" ]; then
  echo "Erstelle virtuelle Umgebung im Ordner '$SCRIPT_DIR/venv'..."
  python3 -m venv "$SCRIPT_DIR/venv"
fi

# Aktiviere die virtuelle Umgebung
source "$SCRIPT_DIR/venv/bin/activate"

# Installiere Abhängigkeiten aus der requirements-Datei (ebenfalls im Skript-Verzeichnis)
pip install --quiet --no-input -r "$SCRIPT_DIR/requirements.txt"

# Starte das CLI-Tool.
# "$@" übergibt alle Parameter, die an das Startskript übergeben werden, 1:1 an python weiter.
python "$SCRIPT_DIR/code_batch_copy.py" "$@"
