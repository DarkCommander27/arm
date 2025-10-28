# 🔗 Bluetooth HID Server Pairing Mode

## What Changed
The **Pair button** now makes your computer act as a **discoverable Bluetooth remote control** that Android TV can find and connect to.

## How It Works

### 🎯 **New Pairing Process**
1. **Press "🔗 Pair" button** → Your computer enters **pairing mode**
2. **Computer becomes discoverable** as "Android TV Remote" 
3. **On Android TV**: Go to Settings → Remote & Accessories → Add accessory
4. **Android TV finds your computer** and connects to it as a remote control
5. **Use remote buttons** to control Android TV

### 🔄 **Button Behavior**
- **First press**: Enter pairing mode (computer becomes discoverable)
- **Second press**: Exit pairing mode (stop advertising)
- **Status shown in app**: "🔵 Pairing mode ON - discoverable to Android TV"

## Files Added/Modified

### New Files
- **`bluetooth_hid_server.py`** - Bluetooth HID server implementation
- **`test_hid_server.py`** - Test script for pairing mode functionality

### Modified Files
- **`main.py`** - Updated Pair button to use HID server instead of client
- **`bluetooth_control.py`** - Enhanced logging for debugging

## Testing the New Functionality

### 1. Test Without GUI (Container-Safe)
```bash
python test_hid_server.py
```
This tests the pairing mode logic without requiring a GUI or real Bluetooth hardware.

### 2. Test With Full App (Requires Bluetooth Hardware)
```bash
python main.py
```
1. Click "🔗 Pair" button
2. Check that status shows "Pairing mode ON"
3. Use Android TV to discover and connect

### 3. Debug Logging
Check `app.log` for detailed pairing mode traces:
```bash
tail -f app.log
```

## Technical Details

### What the HID Server Does
- **Advertises** as a Bluetooth HID (Human Interface Device)
- **Appears** to Android TV as a generic remote control
- **Accepts connections** from Android TV
- **Sends HID reports** when buttons are pressed

### Pairing Mode Timeout
- **Default**: 120 seconds (2 minutes)
- **Automatic exit**: Pairing mode ends after timeout
- **Manual exit**: Press Pair button again to stop early

### Platform Support
- **Linux**: Full support with BlueZ
- **Windows**: Full support with Windows Bluetooth stack  
- **macOS**: Full support with Core Bluetooth
- **Container**: Limited (no real Bluetooth hardware)

## Troubleshooting

### Pairing Mode Doesn't Start
1. **Check Bluetooth availability**:
   ```bash
   python -c "from bluetooth_hid_server import BLUETOOTH_AVAILABLE; print(f'Available: {BLUETOOTH_AVAILABLE}')"
   ```

2. **Check system Bluetooth**:
   - Linux: `sudo systemctl status bluetooth`
   - Windows: Check Bluetooth is enabled in Settings

3. **Check logs**: Look for errors in `app.log`

### Android TV Doesn't Find Device
1. **Ensure Android TV Bluetooth is on**
2. **Go to pairing mode**: Settings → Remote & Accessories → Add accessory
3. **Wait**: Discovery can take 30-60 seconds
4. **Check distance**: Stay within 10 meters during pairing

### Connection Fails
1. **Try unpairing/repairing** if previously connected
2. **Restart Bluetooth** on both devices
3. **Check interference** from other Bluetooth devices

## Command Reference

### Run Pairing Mode Test
```bash
# Basic functionality test (works in container)
python test_hid_server.py

# Full app test (requires Bluetooth hardware)  
python main.py
```

### Check Bluetooth Status
```bash
# Linux
sudo systemctl status bluetooth
hciconfig -a

# Windows (PowerShell)
Get-Service -Name 'bthserv'
```

### View Logs
```bash
# Real-time log monitoring
tail -f app.log

# Last 50 log entries
tail -n 50 app.log
```

## Implementation Notes

### Why This Approach?
- **Standard HID protocol**: Works with any device that supports Bluetooth HID
- **No custom pairing**: Uses standard Bluetooth pairing process
- **Universal compatibility**: Works with Android TV, phones, tablets, computers
- **Professional implementation**: Follows Bluetooth HID specifications

### Previous vs New Behavior
- **Previous**: Send PAIR command to already-connected Android TV
- **New**: Make computer discoverable so Android TV can connect to it
- **Advantage**: No need to manually connect to Android TV first

### Security
- **Standard Bluetooth security**: Uses Bluetooth pairing and encryption
- **Limited exposure**: Only active when explicitly enabled
- **Timeout protection**: Automatically exits pairing mode after 2 minutes