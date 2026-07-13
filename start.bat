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

if exist "%~dp0python\python.exe" (
    echo [INFO] Detected packaged embedded Python environment.
    "%~dp0python\python.exe" scripts\launcher.py --foreground
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO] Embedded Python not found. Using system Python environment...
        python scripts\launcher.py --foreground
    ) else (
        echo.
        echo ===================================================
        echo ❌ 错误：未检测到可用的 Python 运行环境！
        echo ===================================================
        echo 1. 如果您使用的是“绿色分发版”，请检查当前目录下是否存在 python 文件夹。
        echo 2. 如果您是开发者，请先安装 Python 3.12 并将其加入系统环境变量 (PATH)。
        echo ===================================================
        echo.
        pause
        exit /b 1
    )
)
