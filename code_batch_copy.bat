@echo off
setlocal

:: ==========================================
:: KONFIGURATION
:: ==========================================
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "REQ_FILE=%SCRIPT_DIR%requirements.txt"
set "MAIN_SCRIPT=%SCRIPT_DIR%code_batch_copy.py"

:: ==========================================
:: 1. BESTEN PYTHON INTERPRETER FINDEN
:: ==========================================
:: Wir bevorzugen den 'py' Launcher, da er Versionen besser managt.
py -3 -c "exit()" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3"
) else (
    :: Fallback: Prüfen ob 'python' im Pfad ist und ob Version >= 3.9
    python -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON_CMD=python"
    ) else (
        echo [FEHLER] Kein Python 3.9+ gefunden.
        echo Bitte Python installieren: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

:: ==========================================
:: 2. VENV PRÜFEN & REPARIEREN (Selbstheilung)
:: ==========================================
if exist "%VENV_DIR%\Scripts\python.exe" (
    :: Test: Funktioniert das Venv noch? (Geht kaputt bei Pfadänderung)
    "%VENV_DIR%\Scripts\python.exe" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Virtuelle Umgebung defekt. Repariere...
        rmdir /s /q "%VENV_DIR%"
    )
)

:: ==========================================
:: 3. VENV ERSTELLEN (Falls nicht vorhanden)
:: ==========================================
if not exist "%VENV_DIR%" (
    echo [INFO] Erstelle virtuelle Umgebung...
    %PYTHON_CMD% -m venv "%VENV_DIR%"

    :: Pip sofort upgraden, um Warnungen zu vermeiden
    "%VENV_DIR%\Scripts\python.exe" -m pip install --quiet --upgrade pip
)

:: ==========================================
:: 4. ABHÄNGIGKEITEN PRÜFEN (Lazy Install)
:: ==========================================
:: Wir prüfen kurz, ob 'questionary' importierbar ist. Wenn ja, überspringen wir pip install.
"%VENV_DIR%\Scripts\python.exe" -c "import questionary; import pyperclip" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installiere notwendige Pakete...
    "%VENV_DIR%\Scripts\pip.exe" install --quiet --no-input -r "%REQ_FILE%"
)

:: ==========================================
:: 5. STARTEN
:: ==========================================
:: Wir rufen direkt die Python.exe im Venv auf. 'activate' ist in Skripten oft unnötig komplex.
"%VENV_DIR%\Scripts\python.exe" "%MAIN_SCRIPT%" %*

endlocal
