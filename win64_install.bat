@echo off
setlocal enabledelayedexpansion

:: --- Configuration ---
set VENV_NAME=venv
set REQS_FILE=requirements.txt

echo [1/5] Checking for Python 3.12...
:: Check if python is in path and if it's the right version
python --version 2>nul | findstr "3.12" >nul
if %errorlevel% equ 0 (
    echo Python 3.12 is already installed.
) else (
    echo Python 3.12 not found. Attempting automatic installation via WinGet...
    
    :: Use WinGet to install Python 3.12 silently
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    
    if %errorlevel% neq 0 (
        echo [ERROR] WinGet failed to install Python. Please install it manually from python.org.
        pause
        exit /b
    )
    
    :: Refresh path so the current script can see the new installation
    echo Installation successful. Refreshing environment...
    call refreshenv >nul 2>&1 || (
        echo [NOTE] You may need to restart this script for the new Python path to take effect.
    )
)

echo [2/5] Creating virtual environment in .\%VENV_NAME%...
if exist %VENV_NAME% (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv %VENV_NAME%
)

echo [3/5] Upgrading pip inside venv...
call %VENV_NAME%\Scripts\activate
python -m pip install --upgrade pip

echo [4/5] Installing requirements from %REQS_FILE%...
if exist %REQS_FILE% (
    pip install -r %REQS_FILE%
) else (
    echo [SKIP] %REQS_FILE% not found.
)

echo [5/5] Setup complete! 
echo To use your environment, run: call %VENV_NAME%\Scripts\activate
pause