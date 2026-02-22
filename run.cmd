@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting setup...

:: Detect Python (Prefer 3.12 or 3.11 to avoid numpy/agent-zero conflicts on 3.13)
set PYTHON_BIN=
py -3.12 -V >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_BIN=py -3.12
) else (
    py -3.11 -V >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_BIN=py -3.11
    ) else (
        python -V >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            set PYTHON_BIN=python
            for /f "delims=" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VER=%%i
            if "!PY_VER!"=="3.13" set BAD_VER=1
            if "!PY_VER!"=="3.14" set BAD_VER=1
            if "!BAD_VER!"=="1" (
                echo ❌ Error: Python !PY_VER! detected. This causes dependency conflicts with agent-zero and numpy.
                echo Please install Python 3.12 or 3.11 to continue.
                echo After installing, delete the existing .venv folder and run this script again.
                exit /b 1
            )
        ) else (
            echo ❌ Error: Python is not installed or not in PATH.
            exit /b 1
        )
    )
)

:: Create virtual environment if it doesn't exist
if not exist ".venv\" (
    echo 📦 Creating virtual environment using !PYTHON_BIN!...
    !PYTHON_BIN! -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo ❌ Error: Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo ✅ Virtual environment already exists.
    echo ⚠️ If you previously used Python 3.13, please delete the .venv folder and re-run this script.
)

:: Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo ❌ Error: Could not find activation script in .venv\Scripts
    exit /b 1
)

echo 📥 Installing dependencies from requirements.txt...
:: Use only-binary orjson to avoid Rust compiler issues
pip install --only-binary :all: orjson
pip install -r requirements.txt
if !ERRORLEVEL! NEQ 0 (
    echo ❌ Error: Failed to install dependencies.
    exit /b 1
)

echo 🤖 Starting the Telegram Bot...
python agent_zero_telegram_bot.py
