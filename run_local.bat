@echo off
setlocal
cd /d "%~dp0"

echo ============================================================================
echo   Offline Template ^& Variable Field Injector - Local Launcher
echo ============================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating local Python virtual environment ^(.venv^)...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv. Please ensure Python 3.11+ is installed and on PATH.
        pause
        exit /b 1
    )
    echo [2/3] Installing required packages from requirements.txt...
    ".venv\Scripts\pip.exe" install --upgrade pip
    ".venv\Scripts\pip.exe" install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies from requirements.txt.
        pause
        exit /b 1
    )
)

if not exist "assets\app_icon.ico" (
    echo [INFO] Generating application icon asset...
    ".venv\Scripts\python.exe" scripts\generate_icon.py
)

echo [INFO] Launching Offline Template ^& Variable Field Injector...
".venv\Scripts\python.exe" -m src.main
endlocal

