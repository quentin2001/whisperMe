@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo [1/2] Checking for existing whisperMe instances...
powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:9101/api/health' -TimeoutSec 1; if ($r.status -eq 'ok') { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] whisperMe is already running! Opening browser...
    start http://localhost:9101
    exit /b 0
)

if exist .whisperMe.pid (
    set /p PID=<.whisperMe.pid
    taskkill /F /T /PID %PID% >nul 2>&1
    del .whisperMe.pid
)
ping 127.0.0.1 -n 2 > nul

if exist "%~dp0python\python.exe" (
    echo [INFO] Detected packaged embedded Python environment.
    "%~dp0python\python.exe" scripts\lazy_load_env.py
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
        echo 2. 如果您是开发者，请先安装 Python 3.12 并将其加入系统环境变量 PATH 中。
        echo ===================================================
        echo.
        pause
        exit /b 1
    )
)
