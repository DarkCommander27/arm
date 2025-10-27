# Windows PowerShell Build Script for Android TV Remote
# This script builds the application using PyInstaller

Write-Host "Building Android TV Remote for Windows..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and add it to your PATH" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in a virtual environment, if not create one
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "You may need to enable script execution: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install PyInstaller
Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
pip install pyinstaller
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install PyInstaller" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Run tests (optional)
Write-Host ""
Write-Host "Running tests..." -ForegroundColor Yellow
python -m pytest test_bluetooth.py -v
Write-Host "Test results above (some async tests may fail in pytest)" -ForegroundColor Cyan

# Build the application
Write-Host ""
Write-Host "Building application..." -ForegroundColor Yellow
pyinstaller main.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Executable location: dist\AndroidTVRemote.exe" -ForegroundColor Cyan
Write-Host ""

# Optional: Test the built executable
$testRun = Read-Host "Do you want to test run the built executable? (y/n)"
if ($testRun -eq "y" -or $testRun -eq "Y") {
    Write-Host "Starting AndroidTVRemote.exe..." -ForegroundColor Green
    Start-Process "dist\AndroidTVRemote.exe"
}

Write-Host ""
Write-Host "Build process finished." -ForegroundColor Green
Read-Host "Press Enter to exit"