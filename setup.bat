@echo off
REM PBCA Agent Setup Script for Windows

echo ========================================
echo PBCA Agent Setup
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Check Ollama
echo [2/5] Checking Ollama installation...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama is not installed
    echo Please install from: https://ollama.com/download
    echo.
    echo After installing Ollama, run:
    echo   ollama pull mistral
    echo.
) else (
    ollama --version
)
echo.

REM Create virtual environment
echo [3/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo Created virtual environment
)
echo.

REM Activate and install dependencies
echo [4/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo.

REM Check configuration
echo [5/5] Checking configuration...
findstr "YOUR_BOT_TOKEN_HERE" config\settings.py >nul
if not errorlevel 1 (
    echo.
    echo ========================================
    echo IMPORTANT: Configuration Required
    echo ========================================
    echo.
    echo Please edit config\settings.py and set:
    echo   1. TELEGRAM_BOT_TOKEN - Get from @BotFather on Telegram
    echo   2. AUTHORIZED_USER_ID - Get from @userinfobot on Telegram
    echo.
    echo After configuration, run:
    echo   venv\Scripts\activate
    echo   python main.py
    echo.
) else (
    echo Configuration appears to be set
    echo.
    echo To start the agent:
    echo   venv\Scripts\activate
    echo   python main.py
)

echo.
echo ========================================
echo Setup Complete
echo ========================================
pause
