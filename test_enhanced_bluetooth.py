#!/usr/bin/env python3
"""
Test script for enhanced Bluetooth detection and reliability improvements.
This tests the new discovery algorithms, quality scoring, and retry logic.
"""

import asyncio
import logging
import sys
import time

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bluetooth_test.log')
    ]
)

try:
    from bluetooth_enhanced import EnhancedBluetoothDeviceManager, BLUETOOTH_AVAILABLE
    from bluetooth_control import BLUETOOTH_AVAILABLE as CONTROL_AVAILABLE
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all Bluetooth modules are in the same directory")
    sys.exit(1)

async def test_enhanced_bluetooth():
    """Comprehensive test of enhanced Bluetooth functionality."""
    print("=" * 80)
    print("🧪 ENHANCED BLUETOOTH DETECTION TEST")
    print("=" * 80)
    
    # Basic availability check
    print(f"1. Bluetooth module availability:")
    print(f"   - bluetooth_enhanced: {BLUETOOTH_AVAILABLE}")
    print(f"   - bluetooth_control:  {CONTROL_AVAILABLE}")
    
    if not BLUETOOTH_AVAILABLE:
        print("❌ FAIL: Enhanced Bluetooth not available")
        print("Install required package: pip install bleak")
        return False
    
    # Create enhanced manager
    print(f"\n2. Creating enhanced Bluetooth manager...")
    try:
        manager = EnhancedBluetoothDeviceManager()
        print(f"✅ Manager created successfully")
        print(f"   Type: {type(manager).__name__}")
        print(f"   Controller present: {manager.controller is not None}")
    except Exception as e:
        print(f"❌ FAIL: Could not create manager: {e}")
        return False
    
    # Test enhanced discovery
    print(f"\n3. Testing enhanced discovery (3 attempts × 10 seconds)...")
    print(f"   This will take about 30-45 seconds...")
    
    start_time = time.time()
    try:
        devices = await manager.enhanced_discover_devices(timeout=10.0, retry_count=3)
        end_time = time.time()
        
        print(f"✅ Enhanced discovery completed in {end_time - start_time:.1f} seconds")
        print(f"   Found {len(devices)} devices after filtering")
        
        if devices:
            print(f"\n📱 DISCOVERED DEVICES (Top 10):")
            print(f"{'#':<3} {'Name':<25} {'Address':<18} {'RSSI':<6} {'Score':<6} {'Android TV?'}")
            print("-" * 80)
            
            for i, device in enumerate(devices[:10]):
                name = device['name'][:24]
                address = device['address']
                rssi = device.get('rssi', 'N/A')
                score = device.get('quality_score', 0)
                is_tv = manager._is_android_tv_device(device)
                tv_indicator = "📺 YES" if is_tv else "   no"
                
                print(f"{i+1:<3} {name:<25} {address:<18} {rssi!s:<6} {score:<6} {tv_indicator}")
            
            # Analyze results
            tv_devices = [d for d in devices if manager._is_android_tv_device(d)]
            strong_signals = [d for d in devices if d.get('rssi', -100) > -70]
            
            print(f"\n📊 ANALYSIS:")
            print(f"   - Total devices found: {len(devices)}")
            print(f"   - Likely Android TV devices: {len(tv_devices)}")
            print(f"   - Strong signal devices (>-70 dBm): {len(strong_signals)}")
            
            if tv_devices:
                print(f"   🎯 RECOMMENDED TARGETS:")
                for device in tv_devices[:3]:
                    print(f"      → {device['name']} ({device['address']}) Score: {device.get('quality_score', 0)}")
        else:
            print(f"⚠️  No devices found - this might indicate:")
            print(f"      - No Bluetooth devices in range")
            print(f"      - Bluetooth hardware not available") 
            print(f"      - Running in container without Bluetooth access")
            print(f"      - Bluetooth service not running")
        
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test connection retry logic (only if we have devices)
    if devices and len(devices) > 0:
        print(f"\n4. Testing connection retry logic...")
        test_device = devices[0]  # Try the highest-rated device
        print(f"   Testing with: {test_device['name']} ({test_device['address']})")
        
        try:
            # This will likely fail since we're not actually pairing, but tests the retry logic
            success = await manager.connect_with_retry(test_device['address'], max_retries=2)
            if success:
                print(f"✅ Connection test succeeded!")
                await manager.controller.disconnect() if manager.controller else None
            else:
                attempts = manager.get_connection_history(test_device['address'])
                print(f"⚠️  Connection test failed as expected (retry logic worked: {attempts} attempts)")
                
        except Exception as e:
            print(f"⚠️  Connection test error (expected): {e}")
    
    print(f"\n5. Testing quality scoring algorithm...")
    # Test with synthetic device data
    test_devices = [
        {'name': 'Unknown Device', 'address': '00:00:00:00:00:01', 'rssi': -45},
        {'name': 'Android TV Living Room', 'address': '00:00:00:00:00:02', 'rssi': -65},
        {'name': 'iPhone', 'address': '00:00:00:00:00:03', 'rssi': -50},
        {'name': 'Chromecast', 'address': '00:00:00:00:00:04', 'rssi': -80},
        {'name': 'Bluetooth Mouse', 'address': '00:00:00:00:00:05', 'rssi': -40},
    ]
    
    print(f"   Testing quality scoring with sample devices:")
    for device in test_devices:
        score = manager._calculate_device_quality(device)
        is_tv = manager._is_android_tv_device(device)
        device['quality_score'] = score
        print(f"      {device['name']:<25} Score: {score:3d} Android TV: {is_tv}")
    
    # Test sorting
    sorted_devices = manager._sort_and_filter_devices(test_devices)
    print(f"   After sorting and filtering:")
    for i, device in enumerate(sorted_devices):
        print(f"      #{i+1}: {device['name']} (Score: {device['quality_score']})")
    
    print(f"\n✅ Enhanced Bluetooth detection test completed successfully!")
    print(f"=" * 80)
    return True

async def test_discovery_comparison():
    """Compare basic vs enhanced discovery."""
    if not BLUETOOTH_AVAILABLE:
        return
    
    print(f"\n🔄 DISCOVERY COMPARISON TEST")
    print(f"-" * 50)
    
    manager = EnhancedBluetoothDeviceManager()
    
    # Test basic discovery
    print(f"Testing basic discovery (single attempt)...")
    try:
        from bluetooth_control import BluetoothDeviceManager
        basic_manager = BluetoothDeviceManager()
        basic_devices = await basic_manager.discover_devices(timeout=8.0)
        print(f"Basic discovery: {len(basic_devices)} devices")
    except:
        basic_devices = []
        print(f"Basic discovery: Failed or unavailable")
    
    # Test enhanced discovery
    print(f"Testing enhanced discovery (3 attempts with retry)...")
    enhanced_devices = await manager.enhanced_discover_devices(timeout=8.0, retry_count=3)
    print(f"Enhanced discovery: {len(enhanced_devices)} devices")
    
    print(f"\nComparison:")
    print(f"  Basic:    {len(basic_devices)} devices")
    print(f"  Enhanced: {len(enhanced_devices)} devices")
    print(f"  Improvement: +{len(enhanced_devices) - len(basic_devices)} devices")

if __name__ == "__main__":
    try:
        print("Starting enhanced Bluetooth detection tests...\n")
        
        # Main test
        result = asyncio.run(test_enhanced_bluetooth())
        
        # Comparison test
        asyncio.run(test_discovery_comparison())
        
        if result:
            print("\n🎉 All tests completed successfully!")
            print("Enhanced Bluetooth detection is ready for use.")
        else:
            print("\n💥 Some tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)