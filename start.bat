@echo off
echo =============================================
echo   AFL Tipping Leaderboard 2026
echo =============================================
echo.
echo Installing/checking dependencies...
py -m pip install -r requirements.txt --quiet
echo.
echo Starting app...
echo Open http://127.0.0.1:5000 in your browser
echo Press Ctrl+C to stop
echo.
cd /d "%~dp0"
py app.py
pause
