#!/bin/bash
cd "$(dirname "$0")"

echo "正在停止 whisperMe 服务..."

# 1. 通过 PID 文件停止服务
if [ -f .whisperMe.pid ]; then
    PID=$(cat .whisperMe.pid)
    kill -9 "$PID" 2>/dev/null
    rm -f .whisperMe.pid
fi

# 2. 终极兜底：强杀占用 9101 端口的所有残留进程
if command -v lsof >/dev/null 2>&1; then
    LSOF_PID=$(lsof -t -i:9101)
    if [ ! -z "$LSOF_PID" ]; then
        kill -9 $LSOF_PID 2>/dev/null
    fi
fi

echo "whisperMe 服务已成功停止。"
