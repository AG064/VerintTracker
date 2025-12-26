@echo off
REM Quick setup script for Verint Tracker (Windows)

echo ======================================
echo Verint Tracker - Setup Script
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3 is not installed.
    echo Please install Python 3.7 or higher from python.org
    pause
    exit /b 1
)

python --version
echo.

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install Python dependencies.
    pause
    exit /b 1
)

echo.
echo Installing Microsoft Edge browser driver...
playwright install msedge

if errorlevel 1 (
    echo Warning: Failed to install Edge driver.
    echo You may need to install it manually.
)

echo.
echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo Run the verification test:
echo   python test_setup.py
echo.
echo Start the tracker:
echo   python verint_tracker.py
echo.
pause

