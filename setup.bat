@echo off
REM Schwab Options Tracker - Windows Quick Setup Script
echo 🚀 Setting up Schwab Options Tracker...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.9+ and add it to your PATH
    pause
    exit /b 1
)

echo ✅ Python detected

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo ⚙️ Creating .env file from template...
    copy .env.template .env
    echo ⚠️ Please edit .env file with your Schwab API credentials
) else (
    echo ✅ .env file already exists
)

REM Create tokens directory
if not exist "tokens" mkdir tokens

echo 🎉 Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your Schwab API credentials
echo 2. Run: streamlit run main.py
echo 3. Complete OAuth authentication in the web interface
echo.
echo For detailed instructions, see README.md
pause