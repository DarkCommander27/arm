"""
Enhanced Bluetooth Control with Improved Discovery and Connection Reliability.

This module provides enhanced Bluetooth functionality with:
- Multi-attempt discovery with deduplication
- Device quality scoring and intelligent filtering  
- Improved connection retry logic
- Better Android TV device detection
"""

import asyncio
import logging
import struct
import time
from typing import Dict, List, Optional, Callable, Any
from enum import IntEnum

try:
    import bleak
    from bleak import BleakClient, BleakScanner
    from bleak.backends.characteristic import BleakGATTCharacteristic
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    bleak = None
    BleakClient = None
    BleakScanner = None
    BleakGATTCharacteristic = None

_LOGGER = logging.getLogger(__name__)

# Import the existing classes and constants from bluetooth_control
try:
    from bluetooth_control import (
        ConsumerControlCodes, BluetoothRemoteController, 
        HID_SERVICE_UUID, HID_REPORT_UUID
    )
except ImportError:
    # Fallback definitions if import fails
    class ConsumerControlCodes(IntEnum):
        POWER = 0x30
        HOME = 0x223
        BACK = 0x224
        MENU = 0x40
        VOLUME_UP = 0xE9
        VOLUME_DOWN = 0xEA
        VOLUME_MUTE = 0xE2
        CHANNEL_UP = 0x9C
        CHANNEL_DOWN = 0x9D
        PLAY_PAUSE = 0xCD
        UP = 0x42
        DOWN = 0x43
        LEFT = 0x44
        RIGHT = 0x45
        SELECT = 0x41
        PAIR = 0x225

class EnhancedBluetoothDeviceManager:
    """Enhanced Bluetooth device manager with improved discovery and reliability."""
    
    def __init__(self):
        self.controller = BluetoothRemoteController() if BLUETOOTH_AVAILABLE else None
        self.discovered_devices: List[Dict[str, Any]] = []
        self.connection_attempts = {}  # Track failed attempts per device
        
    async def enhanced_discover_devices(self, timeout: float = 15.0, retry_count: int = 3) -> List[Dict[str, Any]]:
        """
        Enhanced device discovery with multiple attempts and deduplication.
        
        Args:
            timeout: Discovery timeout per attempt in seconds
            retry_count: Number of discovery attempts
            
        Returns:
            List of discovered devices with quality scoring
        """
        if not BLUETOOTH_AVAILABLE:
            _LOGGER.warning("Bluetooth not available for enhanced discovery")
            return []
        
        _LOGGER.info(f"Starting enhanced discovery: {retry_count} attempts × {timeout}s each")
        all_devices = {}  # Deduplicate by MAC address
        
        for attempt in range(retry_count):
            _LOGGER.info(f"Discovery attempt {attempt + 1}/{retry_count}")
            
            try:
                # Basic discovery
                discovered = await BleakScanner.discover(timeout=timeout)
                
                attempt_count = 0
                for device in discovered:
                    if not device.address:
                        continue
                        
                    device_info = {
                        'address': device.address,
                        'name': device.name or 'Unknown Device',
                        'rssi': getattr(device, 'rssi', None),
                        'discovery_attempt': attempt + 1,
                        'services': []  # Will be populated during connection
                    }
                    
                    # Calculate quality score
                    device_info['quality_score'] = self._calculate_device_quality(device_info)
                    
                    # Deduplicate - keep device with best quality score
                    addr = device_info['address']
                    if addr not in all_devices or device_info['quality_score'] > all_devices[addr]['quality_score']:
                        all_devices[addr] = device_info
                        
                    attempt_count += 1
                
                _LOGGER.info(f"Attempt {attempt + 1}: Found {attempt_count} devices (unique: {len(all_devices)})")
                
                # Short pause between attempts (but not after last)
                if attempt < retry_count - 1:
                    if attempt_count > 0:
                        await asyncio.sleep(2)  # Brief pause if we found devices
                    else:
                        await asyncio.sleep(5)  # Longer pause if nothing found
                        
            except Exception as exc:
                _LOGGER.error(f"Discovery attempt {attempt + 1} failed: {exc}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(3)
        
        # Convert to list and apply filtering/sorting
        devices = list(all_devices.values())
        devices = self._sort_and_filter_devices(devices)
        
        _LOGGER.info(f"Enhanced discovery complete: {len(devices)} devices after filtering")
        
        # Log top devices for debugging
        for i, device in enumerate(devices[:5]):
            _LOGGER.info(f"  #{i+1}: {device['name']} ({device['address']}) "
                        f"RSSI: {device['rssi']} Score: {device['quality_score']}")
        
        self.discovered_devices = devices
        return devices
    
    def _calculate_device_quality(self, device_info: Dict[str, Any]) -> int:
        """Calculate device quality score for sorting."""
        score = 0
        
        # Signal strength scoring
        rssi = device_info.get('rssi')
        if rssi is not None:
            if rssi > -50:
                score += 50  # Excellent signal
            elif rssi > -70:
                score += 30  # Good signal  
            elif rssi > -85:
                score += 10  # Weak but usable
            # Below -85 gets no points
        
        # Device name scoring
        name = device_info.get('name', '').lower()
        if name and name != 'unknown device':
            score += 20  # Has a real name
            
            # Android TV/media device indicators
            if self._is_android_tv_device(device_info):
                score += 100  # Major bonus for likely targets
                
            # Brand recognition
            known_brands = ['google', 'android', 'chromecast', 'nvidia', 'xiaomi', 'samsung', 'lg', 'sony', 'tcl']
            if any(brand in name for brand in known_brands):
                score += 25
        
        # Penalty for devices that are clearly not TVs
        non_tv_indicators = ['phone', 'headphones', 'earbuds', 'watch', 'fitness', 'mouse', 'keyboard', 'tablet']
        if any(indicator in name for indicator in non_tv_indicators):
            score -= 50
        
        return score
    
    def _is_android_tv_device(self, device_info: Dict[str, Any]) -> bool:
        """Enhanced Android TV detection."""
        name = device_info.get('name', '').lower()
        
        # Strong Android TV indicators
        strong_indicators = [
            'android tv', 'google tv', 'chromecast', 'nvidia shield',
            'mi box', 'fire tv', 'roku', 'smart tv', 'tv box',
            'kodi', 'media player', 'streaming'
        ]
        
        return any(indicator in name for indicator in strong_indicators)
    
    def _sort_and_filter_devices(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort devices by quality and filter out obvious non-targets."""
        filtered = []
        
        for device in devices:
            name = device.get('name', '').lower()
            rssi = device.get('rssi')
            
            # Skip devices with very weak signals unless they look promising
            if rssi is not None and rssi < -90:
                if not self._is_android_tv_device(device):
                    continue
            
            # Skip obviously irrelevant devices
            skip_patterns = ['phone', 'headphone', 'earbud', 'watch', 'fitness', 'mouse', 'keyboard']
            if any(pattern in name for pattern in skip_patterns):
                continue
            
            filtered.append(device)
        
        # Sort by quality score (highest first)
        filtered.sort(key=lambda d: d.get('quality_score', 0), reverse=True)
        
        # Limit results to prevent overwhelming UI
        return filtered[:50]
    
    async def connect_with_retry(self, device_address: str, max_retries: int = 3) -> bool:
        """Connect to device with retry logic."""
        if not self.controller:
            return False
        
        # Track connection attempts
        if device_address not in self.connection_attempts:
            self.connection_attempts[device_address] = 0
        
        for attempt in range(max_retries):
            self.connection_attempts[device_address] += 1
            
            _LOGGER.info(f"Connection attempt {attempt + 1}/{max_retries} to {device_address}")
            
            try:
                success = await self.controller.connect(device_address)
                if success:
                    _LOGGER.info(f"Successfully connected to {device_address}")
                    # Reset failed attempts on successful connection
                    self.connection_attempts[device_address] = 0
                    return True
                else:
                    _LOGGER.warning(f"Connection attempt {attempt + 1} failed")
                    
            except Exception as exc:
                _LOGGER.error(f"Connection attempt {attempt + 1} error: {exc}")
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                _LOGGER.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        _LOGGER.error(f"Failed to connect to {device_address} after {max_retries} attempts")
        return False
    
    def get_connection_history(self, device_address: str) -> int:
        """Get number of failed connection attempts for a device."""
        return self.connection_attempts.get(device_address, 0)
    
    def reset_connection_history(self, device_address: str = None):
        """Reset connection attempt history."""
        if device_address:
            self.connection_attempts.pop(device_address, None)
        else:
            self.connection_attempts.clear()


# Convenience functions for backward compatibility
async def enhanced_discover_devices(timeout: float = 15.0, retry_count: int = 3) -> List[Dict[str, Any]]:
    """Standalone enhanced discovery function."""
    manager = EnhancedBluetoothDeviceManager()
    return await manager.enhanced_discover_devices(timeout, retry_count)


if __name__ == "__main__":
    # Test the enhanced discovery
    async def test_enhanced_discovery():
        print("Testing enhanced Bluetooth discovery...")
        
        if not BLUETOOTH_AVAILABLE:
            print("❌ Bluetooth not available")
            return
        
        manager = EnhancedBluetoothDeviceManager()
        devices = await manager.enhanced_discover_devices(timeout=10, retry_count=2)
        
        print(f"\n✅ Found {len(devices)} devices:")
        for i, device in enumerate(devices[:10]):
            print(f"  {i+1:2d}. {device['name']:<25} {device['address']:<18} "
                  f"RSSI: {device['rssi']:-4} Score: {device['quality_score']:3d}")
    
    asyncio.run(test_enhanced_discovery())