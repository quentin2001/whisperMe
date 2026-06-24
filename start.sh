#!/bin/bash
cd "$(dirname "$0")"
nohup python3 launcher.py > /dev/null 2>&1 &
echo "whisperMe 已在后台启动，浏览器将自动打开。"
echo "停止方式: kill \$(cat .whisperMe.pid)"
