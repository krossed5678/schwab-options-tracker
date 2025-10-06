@echo off
REM OptiFlow Dual App Launcher
REM Starts both main OptiFlow app and backtesting app simultaneously

echo.
echo ================================================
echo    OPTIFLOW DUAL APP LAUNCHER
echo ================================================
echo.
echo Starting both OptiFlow main app and backtester...
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
echo    LAUNCHING OPTIFLOW APPLICATIONS
echo ================================================
echo.

REM Start main OptiFlow app in background
echo 🚀 Starting main OptiFlow app on http://localhost:8503
start "OptiFlow Main" cmd /k "call .venv\Scripts\activate.bat && streamlit run main.py --server.port=8503 --server.headless=false"

REM Wait a moment for main app to start
timeout /t 3 /nobreak > nul

REM Start backtesting app
echo 📊 Starting OptiFlow Backtester on http://localhost:8504
echo.
echo ===============================================
echo    OPTIFLOW APPS RUNNING
echo ===============================================
echo 🎯 Main App:     http://localhost:8503
echo 📊 Backtester:   http://localhost:8504
echo.
echo 💡 Use Ctrl+C in each window to stop the apps
echo 🔄 Apps will sync data automatically
echo ===============================================
echo.

REM Start backtesting app in foreground
call .venv\Scripts\activate.bat
streamlit run backtest_app.py --server.port=8504 --server.headless=false

echo.
echo 👋 OptiFlow Backtester stopped
pause