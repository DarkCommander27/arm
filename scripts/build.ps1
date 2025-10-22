# Windows build script
param(
	[switch]$Installer
)

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

if ($Installer) {
		Write-Host "Building NSIS installer..."
		# Install Chocolatey if not present (CI runners have it, but local may not)
		if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
				Write-Host "Chocolatey not found. Installing Chocolatey..."
				Set-ExecutionPolicy Bypass -Scope Process -Force
				[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
				iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
		}

		# Install NSIS
		choco install nsis -y

		# Read version from version.txt
		$Version = (Get-Content -Path "version.txt").Trim()
		Write-Host "Building installer for version $Version"
		
		# Run makensis with installer script and version
		$ProjectDir = (Get-Location).Path
		$NSISScript = Join-Path $ProjectDir "installer\nsis\installer.nsi"
		makensis.exe "/XPROJECT_DIR=$ProjectDir" "/XVERSION=$Version" "$NSISScript"

		Write-Host "Installer created: AndroidTVRemote-$Version-Installer.exe"
}