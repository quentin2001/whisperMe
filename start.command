#!/bin/bash
# Resolve directory containing this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "[1/2] Checking for existing whisperMe instances..."
if curl -s -f -m 1 http://127.0.0.1:9101/api/health >/dev/null 2>&1; then
    echo "[INFO] whisperMe is already running! Opening browser..."
    if command -v open >/dev/null 2>&1; then
        open http://localhost:9101
    fi
    exit 0
fi

if [ -f .whisperMe.pid ]; then
    PID=$(cat .whisperMe.pid)
    kill -9 "$PID" 2>/dev/null
    rm -f .whisperMe.pid
fi

sleep 1

# Check python environment and run launcher in foreground with visible log terminal
if [ -f "./venv/bin/python" ]; then
    echo "[INFO] Using virtual environment Python..."
    ./venv/bin/python scripts/launcher.py --foreground
elif command -v python3 &>/dev/null; then
    echo "[INFO] Using system python3..."
    python3 scripts/launcher.py --foreground
elif command -v python &>/dev/null; then
    echo "[INFO] Using system python..."
    python scripts/launcher.py --foreground
else
    echo "❌ Error: Python not found!"
    read -p "Press enter to exit..."
    exit 1
fi
