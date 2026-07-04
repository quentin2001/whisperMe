@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo [1/2] Checking and cleaning up old instances...
if exist .whisperMe.pid (
    set /p PID=<.whisperMe.pid
    taskkill /F /T /PID %PID% >nul 2>&1
    del .whisperMe.pid
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9101 ^| findstr /i LISTENING') do (
    if not "%%a"=="0" taskkill /F /T /PID %%a >nul 2>&1
)
ping 127.0.0.1 -n 2 > nul

echo [2/2] Starting whisperMe service...
python scripts\launcher.py --foreground
pause
