@echo off
chcp 65001 >nul 2>&1
title whisperMe
cd /d "%~dp0"
python launcher.py
pause
