@echo off
REM OptiFlow Discord Bot Startup
echo.
echo ================================================
echo        OPTIFLOW DISCORD BOT
echo ================================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo 🤖 Starting OptiFlow Discord Bot...
echo 💡 Make sure you've configured DISCORD_BOT_TOKEN in .env
echo 🔗 Bot will connect to your Discord server
echo.

REM Start Discord bot
python discord_bot.py

echo.
echo 👋 OptiFlow Discord Bot stopped
pause