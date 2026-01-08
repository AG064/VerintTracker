@echo off
setlocal

echo ======================================
echo Verint Tracker - CI Build Script
echo ======================================
echo.
echo This script is intended for GitHub Actions (no pre-created venv).
echo.

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
if exist requirements.txt (
    python -m pip install -r requirements.txt
)

echo Installing/Upgrading PyInstaller and Pillow...
python -m pip install --upgrade pyinstaller pillow

echo.
echo Checking for Logo...
python scripts/setup_icon.py

echo.
echo Building Executable...
echo This may take a few minutes.

REM --collect-all is crucial for customtkinter (themes) and playwright (drivers)
pyinstaller --noconfirm --onefile --windowed --name "VerintTracker" ^
    --collect-all customtkinter ^
    --collect-all playwright ^
    --collect-all plyer ^
    --add-data "src/gui/assets/icon.ico;src/gui/assets" ^
    --icon "src/gui/assets/icon.ico" ^
    app.py

if %errorlevel% neq 0 (
    echo.
    echo Build Failed!
    exit /b %errorlevel%
)

echo.
echo ======================================
echo CI Build Complete!
echo ======================================
echo.
echo The executable is located in the "dist" folder.
