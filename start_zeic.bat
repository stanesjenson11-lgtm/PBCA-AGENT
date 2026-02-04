@echo off
REM Zeic - Startup Script
REM Ensures only one instance runs

echo.
echo ========================================
echo Starting Zeic (PBCA Agent)
echo ========================================
echo.

REM Kill any existing Python instances to prevent conflicts
echo [1/3] Stopping any existing instances...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 3 /nobreak >nul
echo        Done!
echo.

REM Activate virtual environment
echo [2/3] Activating virtual environment...
call venv\Scripts\activate.bat
echo        Done!
echo.

REM Set encoding to UTF-8 to prevent logging crashes
set PYTHONIOENCODING=utf-8

REM Start Zeic
echo [3/3] Starting Zeic...
echo.
echo ========================================
echo Zeic is starting up!  
echo Send a message to your Telegram bot
echo ========================================
echo.

python main.py

pause
