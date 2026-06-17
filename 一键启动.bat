@echo off
chcp 65001 >nul
title whisperMe 一键启动工具

:: 检查当前目录下是否有 start_project.py
if not exist "%~dp0start_project.py" (
    echo 错误：找不到 start_project.py 脚本！
    pause
    exit /b
)

echo 正在通过 Python 启动项目...
python "%~dp0start_project.py"

pause
