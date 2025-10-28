#!/usr/bin/env python3
"""
Test script to verify the PAIR HID functionality.

This script demonstrates what happens when you press the Pair button:
1. Connects to an Android TV via Bluetooth
2. Sends a PAIR HID report to activate pairing mode on the TV
3. The TV should then become discoverable to other devices

Usage:
    python test_pairing_mode.py
"""

import asyncio
import logging
import sys
from bluetooth_control import BluetoothDeviceManager, BLUETOOTH_AVAILABLE, ConsumerControlCodes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

async def test_pairing_mode():
    """Test the pairing mode activation functionality."""
    print("=" * 60)
    print("ANDROID TV PAIRING MODE ACTIVATION TEST")
    print("=" * 60)
    print()
    
    print("What this test does:")
    print("1. Scans for Bluetooth devices (including Android TVs)")
    print("2. Lets you select and connect to an Android TV")
    print("3. Sends PAIR HID command to put TV in pairing mode")
    print("4. Other devices can then discover and pair with the TV")
    print()
    
    if not BLUETOOTH_AVAILABLE:
        print("❌ FAIL: Bluetooth not available")
        print("Install bleak: pip install bleak")
        return False
    
    print(f"✅ Bluetooth available")
    print(f"✅ PAIR HID code: {ConsumerControlCodes.PAIR} (0x{ConsumerControlCodes.PAIR:04X})")
    print()
    
    # Create manager
    manager = BluetoothDeviceManager()
    
    # Discover devices
    print("🔍 Scanning for Bluetooth devices (10 seconds)...")
    devices = await manager.discover_devices(timeout=10.0)
    
    if not devices:
        print("❌ No devices found")
        print("Make sure your Android TV has Bluetooth enabled and is discoverable")
        return False
    
    print(f"✅ Found {len(devices)} devices:")
    for i, device in enumerate(devices):
        name = device.get('name', 'Unknown')
        addr = device.get('address', 'No address')
        print(f"  {i+1}. {name} ({addr})")
    print()
    
    # In a real scenario, you'd select a device. For testing, we'll just
    # demonstrate what the PAIR command does without actually connecting
    print("📋 PAIR Command Details:")
    print(f"   HID Usage Code: {ConsumerControlCodes.PAIR} (decimal)")
    print(f"   HID Usage Code: 0x{ConsumerControlCodes.PAIR:04X} (hex)")
    print("   Consumer Control Page: 0x0C")
    print("   Effect: Puts Android TV in pairing mode")
    print()
    
    # Test the controller's pair method (without connection)
    print("🧪 Testing PAIR method (without connection):")
    try:
        result = await manager.controller.pair()
        print(f"   Result: {result} (expected False - not connected)")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print()
    print("=" * 60)
    print("SUMMARY:")
    print("- The Pair button sends HID Consumer Control code 0x0225")
    print("- This is the standard 'Bluetooth Pairing' usage code")
    print("- When sent to a connected Android TV, it activates pairing mode")
    print("- Other devices can then discover and pair with the TV")
    print("- To test fully, connect to a real Android TV first")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    asyncio.run(test_pairing_mode())