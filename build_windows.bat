@echo off
REM Windows Build Script for Android TV Remote
REM This script builds the application using PyInstaller

echo Building Android TV Remote for Windows...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if we're in a virtual environment, if not create one
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Install PyInstaller
echo Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

REM Run tests (optional)
echo.
echo Running tests...
python -m pytest test_bluetooth.py -v
echo Test results above (some async tests may fail in pytest)

REM Build the application
echo.
echo Building application...
pyinstaller main.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable location: dist\AndroidTVRemote.exe
echo.

REM Optional: Test the built executable
set /p test_run="Do you want to test run the built executable? (y/n): "
if /i "%test_run%"=="y" (
    echo Starting AndroidTVRemote.exe...
    start "" "dist\AndroidTVRemote.exe"
)

echo.
echo Build process finished.
pause