@echo off
echo ============================================
echo   🚀 Mudroom Protocol v2 - Installer (Win)
echo ============================================

:: Step 1: Clear old venv (optional)
IF EXIST venv (
    echo 🔄 Removing old virtual environment...
    rmdir /s /q venv
)

:: Step 2: Create new venv with Python 3.11
echo 🐍 Creating virtual environment...
py -3.11 -m venv venv

:: Step 3: Activate it
call venv\Scripts\activate.bat

:: Step 4: Install requirements
echo 📦 Installing dependencies...
pip install --upgrade pip
pip install -r requirements-locked-py311.txt

:: Step 5: Confirm
echo ✅ Done setting up Mudroom v2!
python --version
where python
echo.
pause