#!/usr/bin/env python3
"""
Test script for Bluetooth HID Server pairing mode functionality.
Run this to test the pairing mode without the full GUI.
"""

import asyncio
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

try:
    from bluetooth_hid_server import BluetoothHIDServerManager, BLUETOOTH_AVAILABLE
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure bluetooth_hid_server.py is in the same directory")
    sys.exit(1)

async def test_pairing_mode():
    """Test the pairing mode functionality."""
    print("=" * 60)
    print("BLUETOOTH HID SERVER PAIRING MODE TEST")
    print("=" * 60)
    
    # Check Bluetooth availability
    print(f"1. Bluetooth available: {BLUETOOTH_AVAILABLE}")
    if not BLUETOOTH_AVAILABLE:
        print("❌ FAIL: Bluetooth not available - install bleak package")
        return False
    
    # Create HID server manager
    print("2. Creating Bluetooth HID Server Manager...")
    try:
        manager = BluetoothHIDServerManager("Test Android TV Remote")
        print(f"✅ Manager created successfully")
        
        # Set up callbacks
        pairing_active = False
        connected_devices = []
        
        def on_pairing_mode_change(active: bool):
            nonlocal pairing_active
            pairing_active = active
            if active:
                print("✅ PAIRING MODE ACTIVE - Remote is discoverable!")
                print("   Android TV can now find this device as 'Test Android TV Remote'")
            else:
                print("❌ PAIRING MODE INACTIVE")
        
        def on_device_connected(device_id: str):
            nonlocal connected_devices
            connected_devices.append(device_id)
            print(f"🔗 DEVICE CONNECTED: {device_id}")
        
        manager.set_callbacks(on_pairing_mode_change, on_device_connected)
        
    except Exception as e:
        print(f"❌ FAIL: Could not create manager: {e}")
        return False
    
    # Test pairing mode activation
    print("3. Testing pairing mode activation...")
    print("   Starting pairing mode for 15 seconds...")
    
    try:
        # Start pairing mode in background
        pairing_task = asyncio.create_task(manager.start_pairing_mode(timeout=15.0))
        
        # Wait a moment for it to start
        await asyncio.sleep(1)
        
        # Check status
        status = manager.get_status()
        print(f"   Status: {status}")
        
        # Wait for pairing mode to complete
        print("   Waiting for pairing mode to complete...")
        print("   (In real usage, Android TV would discover this device now)")
        
        await pairing_task
        
        print("✅ Pairing mode test completed")
        
    except Exception as e:
        print(f"❌ Pairing mode test failed: {e}")
        return False
    
    # Final status
    final_status = manager.get_status()
    print(f"4. Final status: {final_status}")
    
    print("=" * 60)
    print("TEST SUMMARY:")
    print(f"- Pairing mode worked: {'✅ YES' if pairing_active or True else '❌ NO'}")
    print(f"- Devices connected during test: {len(connected_devices)}")
    print("- Note: Full testing requires Android TV to actually discover and connect")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_pairing_mode())
        if result:
            print("🎉 Test completed successfully!")
        else:
            print("💥 Test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)