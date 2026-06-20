@echo off
chcp 65001 >nul
title whisperMe Launcher
cd /d "%~dp0"

if not exist "start_project.py" (
    echo [ERROR] start_project.py not found in this directory!
    pause
    exit /b
)

echo [INFO] Starting whisperMe services via Python...
python start_project.py
pause
