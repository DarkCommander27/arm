<div align="center">
    <h1>� Bluetooth Android TV Remote Control</h1>
    <p>Universal Bluetooth remote control for Android TV devices</p>

[![Actions status](https://github.com/BushlanovDev/android-tv-remote-control-desktop/actions/workflows/check.yml/badge.svg)](https://github.com/BushlanovDev/android-tv-remote-control-desktop/actions) 
[![Python](https://img.shields.io/badge/Python-3.12%2B-brightgreen)](https://www.python.org/downloads/)
[![PyQt](https://img.shields.io/badge/PyQt-5.15.11-brightgreen)](https://pypi.org/project/PyQt5/) 
[![Platform Win32 | Linux | macOS](https://img.shields.io/badge/Platform-Win32%20|%20Linux%20|%20macOS-brightgreen)]() 
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT) 
</div>


## 🌟 Description
**Bluetooth Remote Control for Android TV!** This application connects to your Android TV via Bluetooth and appears as a generic remote control device. 

**How it works:**
The application implements Bluetooth Low Energy (BLE) Human Interface Device (HID) profile to make your computer appear as a standard Bluetooth remote control to Android TV devices. This provides a universal remote control experience without requiring network configuration.

**Features:**
- **Universal Compatibility**: Works with any Android TV that supports Bluetooth HID input
- **Standard Remote Functions**: Power, volume, navigation, channel control, and media buttons
- **Easy Connection**: Simple Bluetooth pairing process
- **App Quick Launch**: Favorite app buttons for quick access
- **Connection History**: Remembers previously connected devices

The remote control has all the basic control capabilities, such as volume control, channel switching, menu navigation, and power control via Bluetooth HID commands.
<div align="center">
  <img src="https://github.com/BushlanovDev/android-tv-remote-control-desktop/blob/main/resources/screenshot.png?raw=true" alt="Android TV Remote Control Desktop Screenshot" width="800" />
</div>

## 🚀 Quick Start
Download the executable file for your platform from the [release page](https://github.com/BushlanovDev/android-tv-remote-control-desktop/releases) and enjoy =)

## 💻 Run from source code
```bash
# Clone project 
git clone https://github.com/BushlanovDev/android-tv-remote-control-desktop.git

# Create and activate virtual venv 
python -m venv venv
source venv/bin/activate

# Install dependencies (includes Bluetooth support)
pip install -r requirements.txt

# Run app
python main.py
```

## 📡 Bluetooth Setup
**Android TV Setup:**
1. Go to Settings > Device Preferences > Remote & Accessories
2. Select "Add accessory"
3. Make your Android TV discoverable

**Computer Setup:**
1. Make sure your computer has Bluetooth capability
2. The app will automatically handle Bluetooth discovery and pairing
3. Click "📡 Connect via Bluetooth" in the app
4. Select your Android TV from the discovered devices
5. Connect and start using your remote!

For detailed Bluetooth setup and troubleshooting, see [BLUETOOTH.md](BLUETOOTH.md).

## 🛠️ Building an executable file
```bash
pip install pyinstaller # or pip install auto-py-to-exe for use gui

pyinstaller --noconfirm --onedir --windowed --icon "./resources/icon32.ico" --hidden-import "zeroconf._utils.ipaddress" --hidden-import "zeroconf._handlers.answers"  "./main.py"
```
