@echo off
REM OptiFlow - Startup Script
REM This script will start your trading dashboard

echo.
echo ================================================
echo           OPTIFLOW - STARTING UP
echo ================================================
echo.

REM Check if virtual environment exists
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    echo ✅ Virtual environment created
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing/updating requirements...
pip install -r requirements.txt --quiet

echo.
echo ================================================
echo    LAUNCHING STREAMLIT DASHBOARD
echo ================================================
echo.
echo 🚀 Starting Streamlit on http://localhost:8503
echo 📱 Mobile notifications are configured in the Alerts tab
echo 💡 Press Ctrl+C to stop the server
echo.

REM Start Streamlit on port 8503
streamlit run main.py --server.port=8503 --server.headless=false

echo.
echo 👋 OptiFlow stopped
pause