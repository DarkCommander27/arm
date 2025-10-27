# Bluetooth Remote Control for Android TV

This document describes the Bluetooth functionality of the Android TV Remote Control application, which appears as a generic Bluetooth remote control to Android TV devices.

## Overview

The application implements a Human Interface Device (HID) profile over Bluetooth Low Energy (BLE) to make your computer appear as a standard remote control to Android TV systems. This provides universal compatibility without requiring network configuration or specific apps on the TV.

## Features

### Bluetooth HID Controller
- **Generic Remote Control**: Appears as a standard Bluetooth remote to Android TV
- **Standard Key Codes**: Uses industry-standard HID Consumer Control codes
- **Full Remote Functionality**: Supports all basic remote control functions:
  - Power, Home, Back, Menu
  - Volume Up/Down/Mute
  - Channel Up/Down
  - D-Pad navigation (Up, Down, Left, Right, Center/OK)
  - Media controls (Play/Pause, Stop, Fast Forward, Rewind)

### User Interface
- **Bluetooth Pairing Dialog**: Dedicated interface for Bluetooth device management
- **Device Discovery**: Automatically scans for nearby Bluetooth devices
- **Smart Filtering**: Identifies likely Android TV devices
- **Connection Management**: Handles pairing, connection, and disconnection
- **Status Monitoring**: Real-time connection status and logging

### Integration
- **Primary Connection Method**: Bluetooth is the main way to connect to Android TV
- **Unified Interface**: Remote control buttons work seamlessly via Bluetooth HID
- **Device History**: Remembers paired devices for quick reconnection

## Requirements

### Software Dependencies
```bash
pip install bleak>=0.22.3
```

### System Requirements
- **Linux**: BlueZ stack (usually pre-installed)
- **Windows**: Windows 10 version 1903+ with Bluetooth LE support
- **macOS**: macOS 10.14+ with Core Bluetooth

### Android TV Requirements
- Android TV with Bluetooth support
- Bluetooth enabled and discoverable
- Android TV version 6.0+ recommended

## Usage Instructions

### 1. Enable Bluetooth on Android TV
1. Go to **Settings** > **Device Preferences** > **Remote & Accessories**
2. Select **Add accessory**
3. Make sure Bluetooth is enabled and the TV is discoverable

### 2. Connect via Bluetooth
1. Open the Android TV Remote Control application
2. Click the **Bluetooth button (📡)** in the top toolbar
3. In the Bluetooth Pairing Dialog:
   - Click **"🔍 Scan for Devices"**
   - Wait for device discovery to complete
   - Select your Android TV from the list (devices with 📺 icon are likely TVs)
   - Click **"📱 Connect to Selected Device"**
4. Wait for the connection to establish

### 3. Using the Remote
Once connected via Bluetooth:
- All remote control buttons work normally
- The status bar shows "🔵 BT: [Device Name]"
- App launching may be limited (use HOME and navigate manually)

### 4. Testing the Connection
- Use the **"🧪 Test Connection"** button in the Bluetooth dialog
- This sends a volume up command to verify the connection works

## Technical Implementation

### Bluetooth HID Profile
The application implements a Bluetooth Low Energy (BLE) HID device using:
- **Service UUID**: `00001812-0000-1000-8000-00805f9b34fb` (HID Service)
- **Characteristic UUID**: `00002a4d-0000-1000-8000-00805f9b34fb` (HID Report)
- **Report Format**: Consumer Control reports with 16-bit usage codes

### HID Usage Codes
Standard Consumer Control usage codes are used for maximum compatibility:
- Power: 0x30
- Home: 0x223
- Back: 0x224
- Menu: 0x40
- Volume Up: 0xE9
- Volume Down: 0xEA
- Volume Mute: 0xE2
- Channel Up: 0x9C
- Channel Down: 0x9D
- Navigation: 0x42-0x45

### Device Discovery
The application scans for BLE devices and identifies potential Android TV devices by:
- Device name patterns (Android TV, Google TV, Chromecast, etc.)
- Service advertisements
- Signal strength (RSSI)

## Troubleshooting

### Common Issues

#### "Bluetooth functionality not available"
**Solution**: Install the required package:
```bash
pip install bleak
```

#### "No devices found during discovery"
**Possible causes**:
- Android TV Bluetooth is disabled
- TV is not in discoverable mode
- Distance/interference issues
- Bluetooth adapter issues on computer

**Solutions**:
1. Ensure Android TV Bluetooth is enabled and discoverable
2. Move closer to the TV
3. Check computer's Bluetooth adapter is working
4. Try the "Show all devices" option to see all nearby devices

#### "Connection failed" or "Connection lost"
**Possible causes**:
- Bluetooth interference
- Device moved out of range
- Power saving modes
- Incompatible device

**Solutions**:
1. Move closer to the Android TV
2. Restart Bluetooth on both devices
3. Clear Bluetooth cache on Android TV
4. Try reconnecting

#### "Commands not working"
**Possible causes**:
- HID profile not properly established
- Incompatible device firmware
- Android TV not accepting HID commands

**Solutions**:
1. Use the "Test Connection" button
2. Try disconnecting and reconnecting
3. Check Android TV remote control settings
4. Verify the device supports HID input

### Limitations

#### App Launching
- Direct app launching may not work via Bluetooth HID
- Use HOME button and navigate manually to apps
- Wi-Fi connection provides better app launching support

#### Compatibility
- Not all Android TV devices support Bluetooth HID input
- Some devices may require specific pairing procedures
- Older Android TV versions may have limited support

#### Performance
- Bluetooth may have slightly higher latency than Wi-Fi
- Range is limited to typical Bluetooth range (~10 meters)
- Interference from other devices may affect performance

## Development Notes

### File Structure
```
bluetooth_control.py     # Core Bluetooth HID controller
bluetooth_dialog.py      # Bluetooth pairing dialog UI
test_bluetooth.py       # Bluetooth functionality tests
```

### Key Classes
- `BluetoothRemoteController`: Main HID controller implementation
- `BluetoothDeviceManager`: Device discovery and connection management
- `BluetoothPairingDialog`: User interface for Bluetooth operations
- `ConsumerControlCodes`: HID usage code constants

### Testing
Run the Bluetooth test suite:
```bash
python test_bluetooth.py
```

This tests imports, device discovery, controller functionality, and UI components.

## Future Enhancements

### Potential Improvements
1. **Audio over Bluetooth**: Support for voice commands via Bluetooth audio
2. **Enhanced App Launching**: Custom protocols for direct app launching
3. **Profile Persistence**: Remember paired devices across sessions
4. **Advanced HID Features**: Keyboard input, mouse emulation
5. **Multi-device Support**: Connect to multiple TVs simultaneously

### Contributing
When contributing to the Bluetooth functionality:
1. Test on multiple Android TV devices
2. Ensure compatibility with different Bluetooth adapters
3. Handle connection errors gracefully
4. Maintain compatibility with existing Wi-Fi functionality
5. Update tests and documentation

## Security Considerations

### Bluetooth Security
- Connections use standard Bluetooth security protocols
- No sensitive data is transmitted
- Only standard HID commands are sent
- Pairing requires physical access to both devices

### Privacy
- No personal data is collected or transmitted
- Device names and addresses are only stored locally
- Connection history is stored in local files only