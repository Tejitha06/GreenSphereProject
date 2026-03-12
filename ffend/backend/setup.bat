@echo off
REM GreenSphere Backend Setup Script for Windows

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║   GreenSphere Flask Backend Setup                  ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Check if backend directory exists
if not exist "backend" (
    echo Error: backend directory not found!
    echo Please run this script from the ffend root directory.
    pause
    exit /b 1
)

cd backend

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Checking for .env file...
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo [IMPORTANT] Edit .env file and add your PlantID API key:
    echo.
    echo   PLANTID_API_KEY=your_api_key_here
    echo.
    echo Get a free API key from: https://plant.id/
    echo.
    pause
)

echo.
echo [5/5] Setup complete!
echo.
echo ╔════════════════════════════════════════════════════╗
echo ║   Ready to start the backend!                      ║
echo ║                                                    ║
echo ║   Run: python run.py                              ║
echo ║                                                    ║
echo ║   Then visit: http://localhost:5000               ║
echo ╚════════════════════════════════════════════════════╝
echo.

pause
