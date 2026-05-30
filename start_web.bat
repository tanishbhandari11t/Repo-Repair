@echo off
echo ============================================
echo     RepoRepair Web Interface
echo ============================================
echo.

REM Check if virtual environment exists
if not exist venv\ (
    echo ERROR: Virtual environment not found!
    echo Run install.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Starting web server...
echo.
echo ============================================
echo   Web Interface: http://localhost:5000
echo ============================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the web app
python web_app.py
