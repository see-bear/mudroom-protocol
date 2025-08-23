@echo off
echo ================================
echo  🔄 Resetting Mudroom venv (3.11)
echo ================================

:: Deactivate existing venv if active (safe even if not active)
call venv\Scripts\deactivate.bat >nul 2>&1

:: Remove old venv
echo 🧹 Deleting old virtual environment...
rmdir /s /q venv

:: Recreate venv using Python 3.11
echo 🐍 Creating new venv with Python 3.11...
py -3.11 -m venv venv

:: Activate the new venv
call venv\Scripts\activate.bat

:: Show Python version to confirm
python --version

:: Optional: Install dependencies
echo 📦 Installing requirements...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ✅ Environment reset and ready.
cmd /k