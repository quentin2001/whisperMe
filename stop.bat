@echo off
cd /d "%~dp0"

echo Stopping whisperMe service...

if exist .whisperMe.pid (
    set /p PID=<.whisperMe.pid
    taskkill /F /PID %PID% >nul 2>&1
    del .whisperMe.pid
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9101 ^| findstr /i LISTENING') do (
    if not "%%a"=="0" (
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo whisperMe service stopped successfully.
pause
