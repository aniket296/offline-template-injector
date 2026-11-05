@echo off
setlocal
cd /d "%~dp0\.."

echo ============================================================================
echo   Offline Template ^& Variable Field Injector - Windows Installer Builder
echo ============================================================================

call "scripts\build_exe.bat"
if errorlevel 1 (
    echo [ERROR] Standalone EXE build failed. Cannot proceed to installer stage.
    exit /b 1
)

set "ISCC_PATH="

if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) else (
    for %%I in (ISCC.exe) do set "ISCC_PATH=%%~$PATH:I"
)

if defined ISCC_PATH (
    echo [INFO] Found Inno Setup Compiler at: "%ISCC_PATH%"
    "%ISCC_PATH%" "installer\setup.iss"
    if errorlevel 1 (
        echo [ERROR] Inno Setup compilation failed!
        exit /b 1
    )
    echo [SUCCESS] Windows Setup Installer generated at:
    echo           %CD%\dist_installer\OfflineTemplateInjector_Setup.exe
    endlocal
    exit /b 0
) else (
    echo.
    echo [NOTICE] Inno Setup 6 ^(ISCC.exe^) was not found on this machine.
    echo          Your standalone executable is ready and fully functional at:
    echo          %CD%\dist\OfflineTemplateInjector.exe
    echo.
    echo          To compile the optional Windows Setup Wizard ^(OfflineTemplateInjector_Setup.exe^),
    echo          install Inno Setup 6 from: https://jrsoftware.org/isdl.php
    echo          and re-run scripts\build_installer.bat.
    endlocal
    exit /b 0
)
