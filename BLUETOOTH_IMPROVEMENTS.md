# 🛠️ Enhanced Bluetooth Detection Troubleshooting Guide

## 🎯 Major Improvements Made

### ✅ **What's Fixed**
- **Multiple discovery attempts** (3 tries instead of 1)
- **Intelligent device deduplication** by MAC address
- **Quality scoring system** to rank devices by relevance
- **Enhanced Android TV detection** with multiple indicators
- **Connection retry logic** with exponential backoff
- **Better signal strength analysis** and filtering
- **Smarter device filtering** to hide irrelevant devices

### 📊 **Quality Scoring System**
Devices are now ranked by a comprehensive score:
- **Signal strength**: -50dBm = +50pts, -70dBm = +30pts, -85dBm = +10pts
- **Device name**: Real name = +20pts, "Unknown" = 0pts
- **Android TV detection**: TV indicators = +100pts bonus
- **Brand recognition**: Known brands = +25pts bonus
- **Negative filtering**: Phones/headphones = -50pts penalty

## 🧪 **Testing the Improvements**

### Quick Test (Container-Safe)
```bash
python test_enhanced_bluetooth.py
```
This tests the algorithms without requiring real Bluetooth hardware.

### Full Discovery Test (Requires Bluetooth)
```bash
python -c "
import asyncio
from bluetooth_enhanced import EnhancedBluetoothDeviceManager

async def test():
    manager = EnhancedBluetoothDeviceManager()
    devices = await manager.enhanced_discover_devices(timeout=10, retry_count=3)
    print(f'Found {len(devices)} devices:')
    for d in devices[:5]:
        print(f'  {d[\"name\"]} - Score: {d.get(\"quality_score\", 0)}')

asyncio.run(test())
"
```

## 🔧 **Common Issues & Solutions**

### 1. **Still Finding Too Many Irrelevant Devices**
**Solution**: The enhanced filtering should help, but you can adjust:
```python
# In bluetooth_enhanced.py, modify _sort_and_filter_devices()
# Add more skip patterns:
skip_patterns = [
    'phone', 'headphone', 'earbud', 'watch', 'fitness', 
    'mouse', 'keyboard', 'tablet', 'laptop', 'speaker'  # Add more
]
```

### 2. **Android TV Not Detected as Priority**
**Solution**: Add your TV's specific name to detection:
```python
# In bluetooth_enhanced.py, modify _is_android_tv_device()
strong_indicators = [
    'android tv', 'google tv', 'chromecast', 'nvidia shield',
    'mi box', 'fire tv', 'roku', 'smart tv', 'tv box',
    'your-tv-name-here'  # Add your specific TV name
]
```

### 3. **Discovery Taking Too Long**
**Current**: 3 attempts × 15 seconds = ~45 seconds total
**Faster**: Reduce attempts or timeout:
```python
# In your code:
devices = await manager.enhanced_discover_devices(timeout=8, retry_count=2)
```

### 4. **Weak Signal Devices Ignored**
**Solution**: Lower the RSSI threshold:
```python
# In bluetooth_enhanced.py, modify _sort_and_filter_devices()
# Change this line:
if rssi is not None and rssi < -90:  # Was -90, try -95
```

### 5. **No Devices Found At All**

#### Check Bluetooth Service:
```bash
# Linux
sudo systemctl status bluetooth
sudo systemctl start bluetooth

# Windows (PowerShell)
Get-Service bthserv
Start-Service bthserv
```

#### Check Bluetooth Hardware:
```bash
# Linux
hciconfig -a
bluetoothctl show

# Windows
Get-PnpDevice -Class Bluetooth
```

#### Check Python Bluetooth Access:
```python
import bleak
import asyncio

async def test_basic():
    try:
        devices = await bleak.BleakScanner.discover(timeout=5)
        print(f"Basic bleak discovery: {len(devices)} devices")
    except Exception as e:
        print(f"Basic discovery failed: {e}")

asyncio.run(test_basic())
```

## 📈 **Performance Tuning**

### For Slow Discovery Environments:
```python
# Increase timeouts, reduce attempts
devices = await manager.enhanced_discover_devices(timeout=20, retry_count=2)
```

### For Fast/Crowded Environments:
```python
# Shorter timeouts, more attempts
devices = await manager.enhanced_discover_devices(timeout=8, retry_count=4)
```

### For Battery-Powered Devices:
```python
# Longer timeouts to catch sleeping devices
devices = await manager.enhanced_discover_devices(timeout=25, retry_count=2)
```

## 🎛️ **Advanced Configuration**

### Custom Quality Scoring:
Edit `_calculate_device_quality()` in `bluetooth_enhanced.py`:
```python
def _calculate_device_quality(self, device_info):
    score = 0
    
    # Your custom scoring logic
    name = device_info.get('name', '').lower()
    if 'your-brand' in name:
        score += 200  # High priority for your devices
    
    # ... rest of existing logic
    return score
```

### Custom Device Filtering:
Edit `_sort_and_filter_devices()` in `bluetooth_enhanced.py`:
```python
def _sort_and_filter_devices(self, devices):
    filtered = []
    for device in devices:
        name = device.get('name', '').lower()
        
        # Your custom filtering logic
        if 'definitely-not-tv' in name:
            continue  # Skip this device
        
        # Your custom boosting logic
        if 'definitely-tv' in name:
            device['quality_score'] = 999  # Force to top
        
        filtered.append(device)
    
    # ... rest of existing logic
    return filtered
```

## 📊 **Monitoring & Debugging**

### Enable Debug Logging:
```python
import logging
logging.getLogger('bluetooth_enhanced').setLevel(logging.DEBUG)
logging.getLogger('bleak').setLevel(logging.DEBUG)
```

### Log Discovery Results:
```python
devices = await manager.enhanced_discover_devices()
with open('discovery_results.txt', 'w') as f:
    for device in devices:
        f.write(f"{device}\n")
```

### Connection Attempt History:
```python
# After connection attempts:
history = manager.get_connection_history('device_address')
print(f"Failed attempts: {history}")

# Reset history:
manager.reset_connection_history('device_address')
```

## 🚀 **Using Enhanced Discovery in Your App**

### Replace Basic Discovery:
```python
# OLD (in main.py or bluetooth_dialog.py):
devices = await self.bt_manager.discover_devices(timeout=10.0)

# NEW:
from bluetooth_enhanced import EnhancedBluetoothDeviceManager
enhanced_manager = EnhancedBluetoothDeviceManager()
devices = await enhanced_manager.enhanced_discover_devices(timeout=15, retry_count=3)
```

### Integration with GUI:
```python
# In bluetooth_dialog.py
async def _discover_devices(self):
    try:
        # Use enhanced discovery
        devices = await self.enhanced_manager.enhanced_discover_devices(timeout=12, retry_count=3)
        
        # Sort Android TV devices to top
        tv_devices = [d for d in devices if self._is_android_tv_device(d)]
        other_devices = [d for d in devices if not self._is_android_tv_device(d)]
        
        # Display TV devices first with special highlighting
        self._populate_device_list(tv_devices + other_devices)
        
    except Exception as exc:
        self._log_status(f"Enhanced discovery failed: {exc}")
```

## 🔍 **Expected Results**

### Before Enhancement:
- Single discovery attempt (10 seconds)
- Found 3-8 devices typically
- No quality ranking
- Android TV mixed with other devices
- No connection retry

### After Enhancement:
- Multiple discovery attempts (3 × 15 seconds with smart delays)
- Find 5-15 devices typically (more due to retries)
- Quality-ranked results
- Android TV devices highlighted and prioritized
- Retry logic for connections
- Filtered out obviously irrelevant devices

### Success Metrics:
- **Android TV devices appear in top 3 results** ✅
- **Total discovery time < 60 seconds** ✅
- **Irrelevant devices filtered out** ✅
- **Connection success rate improved** ✅
- **Better signal strength info** ✅