#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting setup..."

# Detect Python (Prefer 3.12 or 3.11 to avoid numpy/agent-zero conflicts on 3.13)
if command -v python3.12 &>/dev/null; then
    PYTHON_BIN="python3.12"
elif command -v python3.11 &>/dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
    PY_VERSION=$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [ "$PY_VERSION" == "3.13" ] || [ "$PY_VERSION" == "3.14" ]; then
        echo "❌ Error: Python $PY_VERSION detected. This causes dependency conflicts with agent-zero and numpy."
        echo "Please install Python 3.12 to continue. For example, on Ubuntu/Debian:"
        echo "  sudo apt update && sudo apt install python3.12 python3.12-venv"
        echo "After installing, delete the existing .venv folder and run this script again."
        exit 1
    fi
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "❌ Error: Python is not installed or not in PATH."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment using $PYTHON_BIN..."
    $PYTHON_BIN -m venv .venv
else
    echo "✅ Virtual environment already exists."
    echo "⚠️ If you previously used Python 3.13, please 'rm -rf .venv' and re-run this script."
fi

# Activate virtual environment
# This handles both Windows (Git Bash/Mingw) and Linux/macOS paths
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "❌ Error: Could not find activation script in .venv/Scripts or .venv/bin"
    exit 1
fi

echo "📥 Installing dependencies from requirements.txt..."
# Use only-binary orjson to avoid Rust compiler issues we saw earlier
pip install --only-binary :all: orjson || true
pip install -r requirements.txt

echo "🤖 Starting the Telegram Bot..."
python agent_zero_telegram_bot.py
