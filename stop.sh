#!/bin/bash
cd "$(dirname "$0")"
if [ -f .whisperMe.pid ]; then
    PID=$(cat .whisperMe.pid)
    kill "$PID" 2>/dev/null && echo "whisperMe 服务已停止 (PID: $PID)" || echo "进程不存在或已停止。"
    rm -f .whisperMe.pid
else
    echo "whisperMe 未在运行（没有找到 PID 文件）。"
fi
