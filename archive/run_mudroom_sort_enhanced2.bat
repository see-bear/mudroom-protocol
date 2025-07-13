@echo off
setlocal

echo Running Mud Room Sorter Enhanced (Batch + Date Parsing)...

:: Prompt user for a .txt file if none was passed
if "%~1"=="" (
    set /p TXTFILE=Enter transcript filename (.txt): 
) else (
    set TXTFILE=%~1
)

:: Check that the file exists
if not exist "%TXTFILE%" (
    echo ❌ ERROR: File not found: %TXTFILE%
    pause
    exit /b 1
)

python "%~dp0gpt_classifier_enhanced.py" "%TXTFILE%"

echo.
echo ✅ Done. Check gpt_classified\[date]\ for results.
pause
