# Windows build script
$ErrorActionPreference = "Stop"

# Create venv
python -m venv venv
. .\venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Build with spec file
pyinstaller app.spec

Write-Host "Build completed! Check the dist/AndroidTVRemote directory for the output."