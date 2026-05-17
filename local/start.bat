@echo off
echo =============================================
echo   AFL Tipping Leaderboard 2026 (local)
echo =============================================
echo.
cd /d "%~dp0"
py -m pip install -r requirements.txt --quiet
echo.
echo Starting app...
echo Open http://127.0.0.1:5000 in your browser
echo Press Ctrl+C to stop
echo.
py app.py
pause
