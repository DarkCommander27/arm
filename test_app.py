#!/usr/bin/env python3
"""
Test script for the Android TV Remote Control application.
This script tests the core functionality without requiring a display.
"""

import sys
import os
import asyncio
from unittest.mock import patch, MagicMock

# Add the current directory to Python path
sys.path.insert(0, '/workspaces/arm')

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        import history
        print("✓ history.py imported successfully")
        
        import remote_control
        print("✓ remote_control.py imported successfully")
        
        # Test main.py imports without GUI
        with patch.dict('sys.modules', {
            'PyQt5.QtGui': MagicMock(),
            'PyQt5.QtWidgets': MagicMock(),
            'PyQt5.QtCore': MagicMock(),
            'qasync': MagicMock()
        }):
            import main
            print("✓ main.py imported successfully")
            
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_history_functions():
    """Test the history module functions."""
    print("\nTesting history functions...")
    
    try:
        import history
        
        # Test with empty history
        hist = history.get_history()
        print(f"✓ get_history() returned: {len(hist)} items")
        
        # Test adding a device
        history.update_history("Test Device", "192.168.1.100", False)
        hist = history.get_history()
        print(f"✓ Added device, history now has: {len(hist)} items")
        
        # Test favorites
        history.set_favorite("192.168.1.100", True)
        favorites = history.get_favorites()
        print(f"✓ Set favorite, favorites now has: {len(favorites)} items")
        
        return True
    except Exception as e:
        print(f"✗ History test failed: {e}")
        return False

def test_remote_control_class():
    """Test the RemoteControl class initialization."""
    print("\nTesting RemoteControl class...")
    
    try:
        from remote_control import RemoteControl
        
        # Test initialization
        remote = RemoteControl()
        print("✓ RemoteControl initialized successfully")
        
        # Test that it has the expected attributes
        assert hasattr(remote, 'found_addresses')
        assert hasattr(remote, 'remote')
        print("✓ RemoteControl has expected attributes")
        
        # Test command constants
        assert hasattr(remote, 'POWER')
        assert hasattr(remote, 'HOME')
        assert hasattr(remote, 'BACK')
        print("✓ RemoteControl has command constants")
        
        return True
    except Exception as e:
        print(f"✗ RemoteControl test failed: {e}")
        return False

async def test_remote_discovery():
    """Test Android TV discovery (will likely find nothing in codespace)."""
    print("\nTesting Android TV discovery...")
    
    try:
        from remote_control import RemoteControl
        
        remote = RemoteControl()
        
        # This will likely timeout/find nothing in codespace, but should not crash
        addresses = await remote.find_android_tv()
        print(f"✓ Discovery completed, found {len(addresses)} devices")
        
        return True
    except Exception as e:
        print(f"✗ Discovery test failed: {e}")
        return False

def test_gui_creation():
    """Test GUI creation with mocked PyQt5."""
    print("\nTesting GUI creation (mocked)...")
    
    try:
        # Mock all PyQt5 components
        with patch.dict('sys.modules', {
            'PyQt5.QtGui': MagicMock(),
            'PyQt5.QtWidgets': MagicMock(),
            'PyQt5.QtCore': MagicMock(),
            'qasync': MagicMock()
        }):
            # Create mock classes
            mock_qwidget = MagicMock()
            mock_qapplication = MagicMock()
            mock_qsize = MagicMock()
            
            with patch('main.QWidget', mock_qwidget), \
                 patch('main.QApplication', mock_qapplication), \
                 patch('main.QSize', mock_qsize):
                
                from main import MainWindow
                
                # Try to create the window (will be mocked)
                window = MainWindow()
                print("✓ MainWindow created successfully (mocked)")
                
                # Test that it has expected methods
                assert hasattr(window, '_on_pair_new_device')
                assert hasattr(window, '_refresh_device_lists')
                assert hasattr(window, '_on_toggle_favorite')
                print("✓ MainWindow has expected methods")
        
        return True
    except Exception as e:
        print(f"✗ GUI creation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("Android TV Remote Control - Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_history_functions,
        test_remote_control_class,
        test_gui_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    # Run async test
    print("\nRunning async tests...")
    try:
        result = asyncio.run(test_remote_discovery())
        if result:
            passed += 1
        total += 1
    except Exception as e:
        print(f"✗ Async test crashed: {e}")
        total += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application should work correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())