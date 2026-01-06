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
    echo Please install Python 3.10 or higher from python.org
    pause
    exit /b 1
)

python --version
echo.

REM Create Virtual Environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

REM Activate Virtual Environment
echo Activating virtual environment...
call venv\Scripts\activate

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
echo To start the application, run:
echo   run.bat
echo.
pause

