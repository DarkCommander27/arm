#!/usr/bin/env python3
"""
Debug script to test the pairing functionality without the GUI.
This helps isolate whether the issue is in the UI wiring or the Bluetooth controller.
"""

import asyncio
import logging
import sys
from bluetooth_control import BluetoothDeviceManager, BLUETOOTH_AVAILABLE

# Setup logging to see all debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

async def test_pairing():
    """Test the pairing process step by step."""
    print("=" * 50)
    print("PAIR BUTTON DEBUG TEST")
    print("=" * 50)
    
    # Step 1: Check Bluetooth availability
    print(f"1. Bluetooth available: {BLUETOOTH_AVAILABLE}")
    if not BLUETOOTH_AVAILABLE:
        print("❌ FAIL: Bluetooth not available - install bleak package")
        return False
    
    # Step 2: Create manager (like main.py does)
    print("2. Creating BluetoothDeviceManager...")
    try:
        manager = BluetoothDeviceManager()
        print(f"✅ Manager created: {type(manager).__name__}")
        print(f"   Controller present: {manager.controller is not None}")
        print(f"   Controller connected: {manager.controller.is_connected}")
    except Exception as e:
        print(f"❌ FAIL: Could not create manager: {e}")
        return False
    
    # Step 3: Simulate what _on_pair does when NOT connected
    print("3. Testing pair() when NOT connected...")
    print("   (This simulates pressing pair button when no device is connected)")
    
    if not manager.controller.is_connected:
        print("   Not connected - in real app, this would open pairing dialog")
        print("   Let's try calling pair() anyway to see what happens...")
        
        try:
            result = await manager.controller.pair()
            print(f"   pair() returned: {result}")
            if not result:
                print("   ⚠️  Expected: pair() returns False when not connected")
            else:
                print("   ⚠️  Unexpected: pair() returned True despite no connection")
        except Exception as e:
            print(f"   ⚠️  Exception in pair(): {e}")
    
    # Step 4: Test discovery (to see if Bluetooth hardware works)
    print("4. Testing Bluetooth device discovery...")
    try:
        print("   Scanning for 5 seconds...")
        devices = await manager.discover_devices(timeout=5.0)
        print(f"   Found {len(devices)} devices:")
        for i, device in enumerate(devices[:3]):  # Show first 3
            print(f"     {i+1}. {device.get('name', 'Unknown')} - {device.get('address', 'No address')}")
        
        if not devices:
            print("   ⚠️  No devices found - this might indicate:")
            print("      - No Bluetooth hardware available")
            print("      - Bluetooth is disabled") 
            print("      - Running in container without Bluetooth access")
    except Exception as e:
        print(f"   ❌ Discovery failed: {e}")
    
    print("=" * 50)
    print("SUMMARY:")
    print("- If pair() returns False when not connected: EXPECTED")
    print("- If no devices found: likely environment limitation")
    print("- If discovery works: Bluetooth hardware is accessible")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    asyncio.run(test_pairing())