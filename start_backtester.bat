@echo off
REM OptiFlow Backtester - Startup Script
REM This script starts the backtesting web application

echo.
echo ================================================
echo    OPTIFLOW BACKTESTER - STARTING UP
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
echo    LAUNCHING OPTIFLOW BACKTESTER
echo ================================================
echo.
echo 📊 Starting backtesting app on http://localhost:8504
echo 🔄 Will sync with main OptiFlow app if running
echo 💡 Press Ctrl+C to stop the server
echo.

REM Start backtesting Streamlit app on port 8504
streamlit run backtest_app.py --server.port=8504 --server.headless=false

echo.
echo 👋 OptiFlow Backtester stopped
pause