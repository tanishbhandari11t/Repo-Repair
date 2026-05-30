@echo off
echo ========================================
echo RepoRepair Installation Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

echo [4/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [5/5] Setting up environment file...
if not exist .env (
    copy .env.example .env
    echo Created .env file - please edit it with your API keys
) else (
    echo .env already exists - skipping
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your GitHub token and Gemini API key
echo 2. Activate virtual environment: venv\Scripts\activate
echo 3. Run: python -m cli.main config
echo 4. Try: python -m cli.main fix [GITHUB_ISSUE_URL]
echo.
echo See USAGE.md for detailed instructions
echo.
pause
