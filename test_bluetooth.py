#!/usr/bin/env python3
"""
Test script for Bluetooth functionality in Android TV Remote Control.
This script tests the Bluetooth components without requiring the full GUI.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, '/workspaces/arm')

def test_bluetooth_imports():
    """Test Bluetooth module imports."""
    print("Testing Bluetooth imports...")
    
    try:
        from bluetooth_control import BluetoothRemoteController, BluetoothDeviceManager, BLUETOOTH_AVAILABLE
        print(f"✓ Bluetooth imports successful. Available: {BLUETOOTH_AVAILABLE}")
        
        if not BLUETOOTH_AVAILABLE:
            print("⚠️  Bluetooth functionality requires 'bleak' package")
            print("   Install with: pip install bleak")
            return False
        
        from bluetooth_dialog import BluetoothPairingDialog
        print("✓ Bluetooth dialog import successful")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

async def test_bluetooth_discovery():
    """Test Bluetooth device discovery."""
    print("\nTesting Bluetooth device discovery...")
    
    try:
        from bluetooth_control import BluetoothDeviceManager, BLUETOOTH_AVAILABLE
        
        if not BLUETOOTH_AVAILABLE:
            print("⚠️  Skipping discovery test - Bluetooth not available")
            return True
        
        manager = BluetoothDeviceManager()
        print("✓ BluetoothDeviceManager created")
        
        print("🔍 Starting device discovery (10s timeout)...")
        devices = await manager.discover_devices(timeout=5.0)
        
        print(f"✓ Discovery completed. Found {len(devices)} devices:")
        for i, device in enumerate(devices, 1):
            name = device.get('name', 'Unknown')
            address = device.get('address', 'Unknown')
            rssi = device.get('rssi', 'Unknown')
            print(f"  {i}. {name} ({address}) - Signal: {rssi} dBm")
        
        if len(devices) == 0:
            print("ℹ️  No devices found. This is normal if no Bluetooth devices are nearby.")
        
        return True
        
    except Exception as e:
        print(f"✗ Discovery test failed: {e}")
        return False

def test_bluetooth_controller():
    """Test Bluetooth controller class."""
    print("\nTesting Bluetooth controller...")
    
    try:
        from bluetooth_control import BluetoothRemoteController, BLUETOOTH_AVAILABLE
        
        if not BLUETOOTH_AVAILABLE:
            print("⚠️  Skipping controller test - Bluetooth not available")
            return True
        
        controller = BluetoothRemoteController()
        print("✓ BluetoothRemoteController created")
        
        # Test that it has the expected methods
        methods = ['power', 'home', 'back', 'volume_up', 'volume_down', 'dpad_up', 'dpad_center']
        for method in methods:
            if hasattr(controller, method):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} missing")
                return False
        
        # Test device info when not connected
        info = controller.get_device_info()
        if info is None:
            print("✓ get_device_info() returns None when not connected")
        else:
            print(f"✗ get_device_info() should return None when not connected, got: {info}")
            return False
        
        print("✓ Controller tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Controller test failed: {e}")
        return False

def test_hid_constants():
    """Test HID constants and codes."""
    print("\nTesting HID constants...")
    
    try:
        from bluetooth_control import ConsumerControlCodes
        
        # Test that all expected codes exist
        expected_codes = [
            'POWER', 'HOME', 'BACK', 'MENU', 'VOLUME_UP', 'VOLUME_DOWN', 
            'VOLUME_MUTE', 'CHANNEL_UP', 'CHANNEL_DOWN', 'UP', 'DOWN', 
            'LEFT', 'RIGHT', 'SELECT', 'PAIR'
        ]
        
        for code in expected_codes:
            if hasattr(ConsumerControlCodes, code):
                value = getattr(ConsumerControlCodes, code)
                print(f"✓ {code}: 0x{value:04X}")
            else:
                print(f"✗ Missing code: {code}")
                return False
        
        print("✓ HID constants test passed")
        return True
        
    except Exception as e:
        print(f"✗ HID constants test failed: {e}")
        return False

def test_gui_dialog():
    """Test GUI dialog creation (mocked)."""
    print("\nTesting Bluetooth dialog creation...")
    
    try:
        # Mock PyQt5 for testing
        import unittest.mock
        
        with unittest.mock.patch('bluetooth_dialog.QDialog'), \
             unittest.mock.patch('bluetooth_dialog.QVBoxLayout'), \
             unittest.mock.patch('bluetooth_dialog.QPushButton'), \
             unittest.mock.patch('bluetooth_dialog.QListWidget'):
            
            from bluetooth_dialog import BluetoothPairingDialog
            
            # This would normally require a QApplication, but we're mocking
            print("✓ BluetoothPairingDialog import successful (mocked)")
            
        return True
        
    except Exception as e:
        print(f"✗ GUI dialog test failed: {e}")
        return False

async def main():
    """Run all Bluetooth tests."""
    print("=" * 60)
    print("Android TV Remote Control - Bluetooth Test Suite")
    print("=" * 60)
    
    tests = [
        test_bluetooth_imports,
        test_bluetooth_controller,
        test_hid_constants,
        test_gui_dialog,
    ]
    
    async_tests = [
        test_bluetooth_discovery,
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run synchronous tests
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    # Run async tests
    for test in async_tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"✗ Async test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"Bluetooth Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Bluetooth tests passed!")
        print("\nTo use Bluetooth functionality:")
        print("1. Make sure 'bleak' is installed: pip install bleak")
        print("2. Enable Bluetooth on your Android TV")
        print("3. Make your Android TV discoverable")
        print("4. Use the Bluetooth button (📡) in the main app")
        return 0
    else:
        print("❌ Some Bluetooth tests failed.")
        return 1

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted!")
        sys.exit(1)