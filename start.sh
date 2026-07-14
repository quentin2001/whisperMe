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

# Find a suitable system Python (>= 3.10)
PYTHON_BIN=""
for py in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
        if "$py" -c 'import sys; exit(0) if sys.version_info >= (3, 10) else exit(1)' >/dev/null 2>&1; then
            PYTHON_BIN="$py"
            break
        fi
    fi
done

# Check existing venv
if [ -d "venv" ]; then
    # Check if the python inside the existing venv is >= 3.10
    if [ -f "venv/bin/python" ]; then
        VENV_PY="venv/bin/python"
    elif [ -f "venv/bin/python3" ]; then
        VENV_PY="venv/bin/python3"
    else
        VENV_PY=""
    fi

    if [ ! -z "$VENV_PY" ] && "$VENV_PY" -c 'import sys; exit(0) if sys.version_info >= (3, 10) else exit(1)' >/dev/null 2>&1; then
        echo "[INFO] Existing virtual environment is valid (Python >= 3.10)."
    else
        echo "[WARNING] Existing virtual environment is invalid or uses Python < 3.10."
        if [ -z "$PYTHON_BIN" ]; then
            echo "❌ Error: Cannot recreate virtual environment because no Python 3.10+ was found on your system."
            exit 1
        fi
        echo "[INFO] Recreating virtual environment..."
        rm -rf venv
    fi
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    if [ -z "$PYTHON_BIN" ]; then
        echo "==================================================="
        echo "❌ Error: Python 3.10 or newer is required!"
        echo "==================================================="
        echo "Current system Python: $(python3 --version 2>/dev/null || echo 'not found')"
        echo "Please install Python 3.10+ (recommended: 3.12) and try again."
        echo "On macOS, you can install it via Homebrew: brew install python@3.12"
        echo "==================================================="
        exit 1
    fi
    echo "[INFO] Creating virtual environment using $PYTHON_BIN..."
    "$PYTHON_BIN" -m venv venv
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
