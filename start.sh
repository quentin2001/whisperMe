#!/bin/bash
# Resolve directory containing this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "[1/2] Checking and cleaning up old instances..."
if [ -f .whisperMe.pid ]; then
    PID=$(cat .whisperMe.pid)
    kill -9 "$PID" 2>/dev/null
    rm -f .whisperMe.pid
fi

# Also check port 9101
if lsof -Pi :9101 -sTCP:LISTEN -t >/dev/null ; then
    lsof -Pi :9101 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
fi

sleep 1

# Check python environment
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
    exit 1
fi
