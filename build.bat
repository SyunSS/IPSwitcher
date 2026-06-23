@echo off
:: IP Switcher - PyInstaller build script
:: Run from the ip-switcher\ directory as Administrator (or in a venv).

setlocal

set APP_NAME=IPSwitcher
set MAIN_SCRIPT=main.py

:: -- Ensure dependencies are installed --------------------------------
pip install -r requirements.txt --quiet

:: -- Build single-file Windows executable -----------------------------
pyinstaller --noconfirm --clean --onefile --windowed --uac-admin --name "%APP_NAME%" --add-data "ui;ui" --add-data "core;core" "%MAIN_SCRIPT%"

:: Note: --windowed suppresses the console window (GUI app).
::       Remove it if you want a console for debugging.

if %ERRORLEVEL% == 0 (
    echo.
    echo Build succeeded!  Output: dist\%APP_NAME%.exe
) else (
    echo.
    echo Build FAILED.  Check the output above for errors.
)

endlocal
pause
