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
pip install pyinstaller --upgrade

echo.
echo Building Executable...
echo This may take a few minutes.

REM --collect-all is crucial for customtkinter (themes) and playwright (drivers)
pyinstaller --noconfirm --onefile --windowed --name "VerintTracker" ^
    --collect-all customtkinter ^
    --collect-all playwright ^
    --collect-all plyer ^
    --hidden-import "pynput.keyboard._win32" ^
    --hidden-import "pynput.mouse._win32" ^
    app.py

if errorlevel 1 (
    echo.
    echo Build Failed!
    pause
    exit /b 1
)

echo.
echo Copying config file to dist folder...
copy config.json dist\config.json >nul

echo.
echo ======================================
echo Build Complete!
echo ======================================
echo.
echo The executable is located in the "dist" folder.
echo You can copy "VerintTracker.exe" and "config.json" to any location.
echo Note: The first run might be slightly slower as it unpacks dependencies.
echo.
pause
