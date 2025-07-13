@echo off
setlocal EnableDelayedExpansion

echo ===========================================
echo      Mud Room Sorter (Enhanced v5.1)
echo ===========================================
echo.

:: Prompt user for .txt file if not passed as argument
if "%~1"=="" (
    set /p TXTFILE=Enter the path to your transcript (.txt): 
) else (
    set TXTFILE=%~1
)

:: Resolve relative paths if needed
for %%I in ("%TXTFILE%") do set "FULLPATH=%%~fI"

:: Verify file exists
if not exist "!FULLPATH!" (
    echo ❌ ERROR: File not found at: !FULLPATH!
    pause
    exit /b 1
)

:: Run the classifier script
echo Running classifier on:
echo !FULLPATH!
echo.

python "%~dp0gpt_classifier_enhanced.py" "!FULLPATH!"

echo.
echo ✅ All done. Check gpt_classified\[date]\ for output files.
pause