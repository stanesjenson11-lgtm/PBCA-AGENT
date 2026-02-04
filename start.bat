@echo off
REM Quick start script for PBCA Agent

echo Starting PBCA Agent...
echo.

REM Kill any existing Python instances from this folder to avoid conflicts
taskkill /F /FI "WINDOWTITLE eq *pbca-agent*" >nul 2>&1

REM Activate venv and run
call venv\Scripts\activate.bat
python main.py
