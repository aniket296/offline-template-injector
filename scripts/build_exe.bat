@echo off
setlocal
cd /d "%~dp0\.."

echo ============================================================================
echo   Offline Template ^& Variable Field Injector - Standalone EXE Builder
echo ============================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv not found. Please set up .venv first.
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo [1/4] Running automated unit test suite ^(pytest^)...
".venv\Scripts\pytest.exe" -q
if errorlevel 1 (
    echo [ERROR] Unit tests failed! Aborting executable build.
    exit /b 1
)

echo [2/4] Ensuring multi-resolution application icon ^(assets\app_icon.ico^)...
".venv\Scripts\python.exe" scripts\generate_icon.py
if errorlevel 1 (
    echo [ERROR] Icon generation failed!
    exit /b 1
)

echo [3/4] Running PyInstaller with build_windows.spec...
".venv\Scripts\pyinstaller.exe" --noconfirm --clean build_windows.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    exit /b 1
)

echo [4/4] Verifying output binary...
if not exist "dist\OfflineTemplateInjector.exe" (
    echo [ERROR] dist\OfflineTemplateInjector.exe was not found after build!
    exit /b 1
)

echo [SUCCESS] Standalone Windows executable built at:
echo           %CD%\dist\OfflineTemplateInjector.exe
endlocal
exit /b 0

