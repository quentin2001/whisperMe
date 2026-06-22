@echo off
chcp 65001 >nul
title whisperMe Launcher
cd /d "%~dp0"

if not exist "start_project.py" (
    echo [ERROR] start_project.py not found in this directory!
    pause
    exit /b
)
:loop
echo [INFO] Starting whisperMe services via Python...
python start_project.py
echo ========================================
echo ⚠️ 服务意外终止或已退出，将在 3 秒后自动重新启动...
echo 如果需要彻底退出，请直接关闭窗口或按 Ctrl+C。
echo ========================================
timeout /t 3
goto loop
