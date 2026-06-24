@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

REM 通过 PID 文件停止服务
if exist .whisperMe.pid (
    set /p PID=<.whisperMe.pid
    taskkill /F /PID %PID% >nul 2>&1
    del .whisperMe.pid
    echo whisperMe 服务已停止。
) else (
    echo whisperMe 未在运行（没有找到 PID 文件）。
)
pause
