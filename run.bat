@echo off
echo Starting Verint Tracker...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
)
python app.py
pause
