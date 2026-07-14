#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "[1/2] Checking and cleaning up old instances..."
if [ -f .whisperMe.pid ]; then
    PID=$(cat .whisperMe.pid)
    kill -9 $PID 2>/dev/null
    rm .whisperMe.pid
fi

# Find and kill any process listening on 9101
if command -v lsof >/dev/null 2>&1; then
    PIDS=$(lsof -t -i:9101)
    if [ ! -z "$PIDS" ]; then
        kill -9 $PIDS 2>/dev/null
    fi
fi

echo "[INFO] Checking Python environment..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "==================================================="
    echo "❌ Error: Python 3 not found!"
    echo "==================================================="
    echo "Please install Python 3.12 or newer and try again."
    echo "==================================================="
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create virtual environment."
        exit 1
    fi
fi

# Activate venv
source venv/bin/activate

echo "[INFO] Installing dependencies..."
pip install -r backend/requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install dependencies."
    exit 1
fi

echo "[INFO] Starting whisperMe..."
python scripts/launcher.py --foreground
