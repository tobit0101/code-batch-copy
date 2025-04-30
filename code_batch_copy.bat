@echo off

REM Ermittelt den absoluten Pfad des Verzeichnisses, in dem diese Batch-Datei liegt
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM Prüfen, ob die virtuelle Umgebung existiert
IF NOT EXIST "%SCRIPT_DIR%\venv" (
    echo Erstelle virtuelle Umgebung im Ordner "%SCRIPT_DIR%\venv"...
    python -m venv "%SCRIPT_DIR%\venv"
)

REM Aktivieren der virtuellen Umgebung
call "%SCRIPT_DIR%\venv\Scripts\activate.bat"

REM Abhängigkeiten installieren (falls notwendig)
pip install --quiet --no-input -r "%SCRIPT_DIR%\requirements.txt"

REM CLI-Tool starten
REM Falls ein Argument übergeben wird, wird es an das Python-Skript weitergeleitet
python "%SCRIPT_DIR%\code_batch_copy.py" %*

REM Virtuelle Umgebung deaktivieren
deactivate
