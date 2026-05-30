@echo off
echo ========================================
echo RepoRepair Quick Test
echo ========================================
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

echo Your RepoRepair is ready to test!
echo.
echo ========================================
echo Quick Test Commands:
echo ========================================
echo.
echo 1. Check configuration:
echo    py -m cli.main config
echo.
echo 2. Test with dry-run (no PR created):
echo    py -m cli.main fix YOUR_ISSUE_URL --dry-run --skip-tests
echo.
echo 3. Create actual draft PR:
echo    py -m cli.main fix YOUR_ISSUE_URL
echo.
echo ========================================
echo.

:menu
echo What would you like to do?
echo.
echo [1] Check configuration
echo [2] Run dry-run test (you provide issue URL)
echo [3] Create draft PR (you provide issue URL)
echo [4] Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running configuration check...
    py -m cli.main config
    echo.
    goto menu
)

if "%choice%"=="2" (
    echo.
    set /p issue_url="Enter GitHub issue URL: "
    echo.
    echo Running dry-run test...
    py -m cli.main fix %issue_url% --dry-run --skip-tests --verbose
    echo.
    goto menu
)

if "%choice%"=="3" (
    echo.
    set /p issue_url="Enter GitHub issue URL: "
    echo.
    echo WARNING: This will create a DRAFT Pull Request!
    set /p confirm="Are you sure? (y/n): "
    if /i "%confirm%"=="y" (
        echo.
        echo Creating draft PR...
        py -m cli.main fix %issue_url% --verbose
    )
    echo.
    goto menu
)

if "%choice%"=="4" (
    echo.
    echo Goodbye!
    exit /b 0
)

echo Invalid choice. Please try again.
echo.
goto menu
