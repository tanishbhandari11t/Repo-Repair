@echo off
echo ========================================
echo RepoRepair - Simple Test
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Testing with simplified version...
echo This version works without ChromaDB
echo.

python -m cli.main_simple fix https://github.com/zed-industries/zed/issues/6917 --verbose

echo.
echo ========================================
echo.
pause
