@echo off
echo 🚀 Starting ngrok tunnel for Schwab OAuth...
echo.
echo This will create a tunnel from https://51fd616d472e.ngrok-free.app to http://localhost:8080
echo.
echo Make sure you have:
echo 1. Updated your Schwab app redirect URI to: https://51fd616d472e.ngrok-free.app/callback  
echo 2. Updated your .env SCHWAB_REDIRECT_URI to match
echo.
pause

ngrok http 8080 --domain=51fd616d472e.ngrok-free.app

pause