@echo off
setlocal
cd /d "%~dp0"

:: 1. Create a virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating self-contained environment...
    python -m venv .venv
)

:: 2. Activate the environment and check for Tkinter
echo Activating environment...
call .venv\Scripts\activate

python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Tkinter is missing from your Python installation.
    echo Please re-run the Python installer and check "tcl/tk and IDLE".
    pause
    exit /b
)

:: 3. Install/Update dependencies
echo Installing requirements...
python -m pip install --upgrade pip
:: Assumes you have a requirements.txt file in the same folder
if exist "requirements.txt" (
    python -m pip install -r requirements.txt
)

:: 4. Launch your GUI
echo Starting dev_gui.py...
python dev_gui.py

pause
