#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting setup..."

# Detect Python
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "❌ Error: Python is not installed or not in PATH."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_BIN -m venv .venv
else
    echo "✅ Virtual environment already exists."
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
