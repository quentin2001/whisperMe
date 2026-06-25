@echo off
chcp 65001 >nul
title whisperMe Launcher
cd /d "%~dp0"

if not exist "start_project.py" (
    echo [ERROR] start_project.py not found!
    pause
    exit /b
)

:loop
echo [INFO] Starting whisperMe services...
python start_project.py
echo ========================================
echo [WARNING] Services stopped. Restarting in 3 seconds...
echo Close this window or press Ctrl+C to exit.
echo ========================================
timeout /t 3
goto loop
