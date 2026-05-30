@echo off
echo ========================================
echo RepoRepair Quick Test
echo ========================================
echo.
echo Testing with: zed-industries/zed issue #6917
echo.

call venv\Scripts\activate.bat

echo Running RepoRepair...
echo.

py -m cli.main fix https://github.com/zed-industries/zed/issues/6917 --dry-run --skip-tests --verbose

echo.
echo ========================================
echo Test Complete!
echo ========================================
pause
