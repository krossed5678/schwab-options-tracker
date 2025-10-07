@echo off
REM OptiFlow Main App - Simple Startup
echo.
echo ================================================
echo           OPTIFLOW MAIN APP
echo ================================================
echo.

REM Activate virtual environment (assumed to exist)
call .venv\Scripts\activate.bat

echo 🚀 Starting OptiFlow dashboard...
echo 🔗 App will be available at: http://localhost:8503
echo 💡 Press Ctrl+C to stop
echo.

REM Start Streamlit
streamlit run main.py --server.port=8503

echo.
echo 👋 OptiFlow stopped
pause