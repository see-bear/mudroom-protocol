@echo off
echo Running Mud Room Sorter enhanced (Batch + Date Parsing)...

:: Adjusted to run the Python classifier properly
python "%~dp0gpt_classifier_enhanced.py" "%~1"

echo.
echo Done. Check gpt_classified\[date]\ for results.
pause

