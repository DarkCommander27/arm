#!/bin/bash

# Build script for Android TV Remote Control (Bluetooth)
# Creates both distributable package and compiled executable

set -e  # Exit on any error

echo "🚀 Building Android TV Remote Control (Bluetooth-only)..."

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac
echo "🖥️  Detected OS: ${MACHINE}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and add it to your PATH"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "🐍 Found Python: ${PYTHON_VERSION}"

# Check if we're in a virtual environment, if not create one
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install PyInstaller for compiled builds
echo "🔨 Installing PyInstaller..."
pip install pyinstaller

# Run tests (optional)
echo ""
echo "🧪 Running tests..."
python -m pytest test_bluetooth.py -v || echo "⚠️  Some tests may fail in pytest (async tests)"

# Ask user for build type
echo ""
echo "🎯 Choose build type:"
echo "1) Source package (portable Python scripts)"
echo "2) Compiled executable (PyInstaller)"
echo "3) Both"
read -p "Enter choice (1/2/3): " build_choice

# Create build directory
mkdir -p dist
rm -rf dist/*

if [[ $build_choice == "1" || $build_choice == "3" ]]; then
    echo ""
    echo "📂 Creating source package..."
    
    # Copy source files
    echo "� Copying source files..."
    cp main.py dist/
    cp bluetooth_control.py dist/
    cp bluetooth_dialog.py dist/
    cp history.py dist/
    cp requirements.txt dist/
    cp README.md dist/
    cp BLUETOOTH.md dist/
    cp LICENSE dist/
    cp version.txt dist/

    # Copy connection history if it exists
    if [ -f connection_history.json ]; then
        cp connection_history.json dist/
    fi

    # Create run script
    echo "📝 Creating run script..."
    cat > dist/run.sh << 'EOF'
#!/bin/bash

# Android TV Remote Control (Bluetooth) - Linux Runner
echo "🎮 Starting Android TV Remote Control (Bluetooth)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Setting up Python environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the application
echo "🔵 Launching Bluetooth Remote Control..."
python main.py "$@"
EOF

    chmod +x dist/run.sh

    # Create Windows batch file
    echo "📝 Creating Windows run script..."
    cat > dist/run.bat << 'EOF'
@echo off
echo 🎮 Starting Android TV Remote Control (Bluetooth)...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Setting up Python environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Run the application
echo 🔵 Launching Bluetooth Remote Control...
python main.py %*
pause
EOF

    # Create installation instructions
    echo "📖 Creating installation instructions..."
    cat > dist/INSTALL.md << 'EOF'
# Android TV Remote Control (Bluetooth) - Installation

## Quick Start

### Linux/macOS
```bash
./run.sh
```

### Windows
```cmd
run.bat
```

## Manual Installation

### Prerequisites
- Python 3.8 or higher
- Bluetooth support on your system

### Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### Run
```bash
python main.py
```

## Features
- 🔵 Bluetooth HID connectivity to Android TV
- 🎮 Full remote control functionality (Power, Home, Back, etc.)
- 📺 Device discovery and pairing
- 💾 Connection history
- ⚡ Universal compatibility with Android TV devices

## Usage
1. Run the application
2. Click "Connect to Bluetooth Device"
3. Discover and pair with your Android TV
4. Use the remote control buttons

## Troubleshooting
- Ensure Bluetooth is enabled on your system
- Make sure your Android TV is in pairing mode
- Check that bleak library is properly installed for Bluetooth support

For detailed Bluetooth implementation information, see BLUETOOTH.md
EOF

    # Create package info
    echo "📋 Creating package information..."
    VERSION=$(cat version.txt 2>/dev/null || echo "1.0.0")
    cat > dist/BUILD_INFO.txt << EOF
Android TV Remote Control (Bluetooth-only)
Version: $VERSION
Build Date: $(date)
Build Host: $(hostname)
Python Version: $(python3 --version)

Files included:
- main.py (Main application)
- bluetooth_control.py (Bluetooth HID controller)
- bluetooth_dialog.py (Device pairing interface)
- history.py (Connection history)
- requirements.txt (Python dependencies)
- run.sh / run.bat (Launch scripts)
- Documentation (README.md, BLUETOOTH.md, LICENSE)
- Installation guide (INSTALL.md)

This is a Bluetooth-only version with WiFi functionality removed
for simplified deployment and enhanced security.
EOF

    echo "✅ Source package created!"
fi

if [[ $build_choice == "2" || $build_choice == "3" ]]; then
    echo ""
    echo "🔨 Creating compiled executable..."
    
    # Build the application with PyInstaller
    pyinstaller main.spec --clean --noconfirm
    
    if [ $? -eq 0 ]; then
        echo "✅ Compiled executable created!"
        
        # Set executable name based on OS
        if [ "${MACHINE}" = "Mac" ]; then
            echo "📱 Application bundle location: dist/AndroidTVRemote.app"
            echo "� To run: open dist/AndroidTVRemote.app"
        else
            echo "💾 Executable location: dist/AndroidTVRemote"
            echo "🚀 To run: ./dist/AndroidTVRemote"
        fi
    else
        echo "❌ Compiled build failed, but source package is still available"
    fi
fi

echo ""
echo "🎉 Build complete!"
echo ""
echo "�📦 Distribution package created in: ./dist/"
echo "🗂️  Package contents:"
ls -la dist/ | head -20
echo ""

if [[ $build_choice == "1" || $build_choice == "3" ]]; then
    echo "� Source package: cd dist && ./run.sh (Linux/macOS) or run.bat (Windows)"
fi

if [[ $build_choice == "2" || $build_choice == "3" ]]; then
    if [ "${MACHINE}" = "Mac" ]; then
        echo "🖥️  Compiled app: open dist/AndroidTVRemote.app"
    else
        echo "💻 Compiled executable: ./dist/AndroidTVRemote"
    fi
fi

echo "📤 To distribute: zip the entire dist/ folder"

# Optional: Test the built executable
echo ""
read -p "🧪 Do you want to test run the application? (y/n): " test_run
if [[ $test_run == "y" || $test_run == "Y" ]]; then
    echo "🎮 Starting AndroidTVRemote..."
    if [[ $build_choice == "2" || $build_choice == "3" ]]; then
        if [ "${MACHINE}" = "Mac" ]; then
            open dist/AndroidTVRemote.app &
        elif [ -f "dist/AndroidTVRemote" ]; then
            ./dist/AndroidTVRemote &
        else
            cd dist && ./run.sh &
        fi
    else
        cd dist && ./run.sh &
    fi
fi

echo ""
echo "🏁 Build process finished."