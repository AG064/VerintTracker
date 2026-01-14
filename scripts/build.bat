@echo off
echo ======================================
echo Verint Tracker - Build Script
echo ======================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate
)

echo Installing/Upgrading PyInstaller...
pip install pyinstaller pillow --upgrade
pip install -r requirements.txt

echo.
echo Checking for Logo...
python scripts/setup_icon.py

echo.
echo Building Executable from Spec...
echo This may take a few minutes.

pyinstaller --noconfirm --clean VerintTracker.spec

if errorlevel 1 (
    echo.
    echo Build Failed!
    pause
    exit /b 1
)

echo.
echo ======================================
echo Build Complete!
echo File is located in: dist\VerintTracker.exe
echo ======================================
echo.
echo The executable is located in the "dist" folder.
echo You can copy "VerintTracker.exe" to any location.
echo Configuration is now stored in %LOCALAPPDATA%\VerintTracker\config.json
echo Note: The first run might be slightly slower as it unpacks dependencies.
echo.
