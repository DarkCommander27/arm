"""
Bluetooth pairing dialog for Android TV Remote Control.

This module provides a user interface for discovering, pairing, and connecting
to Bluetooth-enabled Android TV devices.
"""

import asyncio
import logging
from typing import Optional, List, Dict

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QProgressBar, QTextEdit,
    QAbstractItemView, QMessageBox, QCheckBox
)

from bluetooth_control import BluetoothDeviceManager, BLUETOOTH_AVAILABLE
from bluetooth_enhanced import EnhancedBluetoothDeviceManager

_LOGGER = logging.getLogger(__name__)


class BluetoothPairingDialog(QDialog):
    """
    Dialog for Bluetooth device discovery and pairing with Android TV.
    
    Provides a user-friendly interface for:
    - Discovering nearby Bluetooth devices
    - Filtering for Android TV devices
    - Managing connections
    - Showing connection status
    """
    
    # Signal emitted when successfully connected to a device
    device_connected = pyqtSignal(dict)  # device_info dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Bluetooth Pairing - Android TV Remote')
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        # Bluetooth manager - use enhanced version
        self.bt_manager = EnhancedBluetoothDeviceManager() if BLUETOOTH_AVAILABLE else None
        self.selected_device: Optional[Dict[str, str]] = None
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self._check_connection_status)
        
        self._setup_ui()
        self._setup_styling()
        
        if not BLUETOOTH_AVAILABLE:
            self._show_bluetooth_unavailable()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title and instructions
        title_label = QLabel('Bluetooth Android TV Connection')
        title_label.setStyleSheet('font-size: 16px; font-weight: bold; color: #ffffff;')
        layout.addWidget(title_label)
        
        instructions = QLabel(
            'Make sure your Android TV has Bluetooth enabled and is discoverable.\n'
            'You may need to go to Settings > Device Preferences > Remote & Accessories '
            'on your Android TV.'
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet('color: #cccccc; font-size: 11px;')
        layout.addWidget(instructions)
        
        # Discovery controls
        discovery_layout = QHBoxLayout()
        
        self.scan_button = QPushButton('🔍 Enhanced Scan')
        self.scan_button.clicked.connect(self._start_discovery)
        discovery_layout.addWidget(self.scan_button)
        
        self.quick_scan_button = QPushButton('⚡ Quick Scan')
        self.quick_scan_button.clicked.connect(self._start_quick_discovery)
        discovery_layout.addWidget(self.quick_scan_button)
        
        self.manual_button = QPushButton('✏️ Manual Entry')
        self.manual_button.clicked.connect(self._manual_device_entry)
        discovery_layout.addWidget(self.manual_button)
        
        discovery_layout.addStretch()
        layout.addLayout(discovery_layout)
        
        # Discovery options
        options_layout = QHBoxLayout()
        
        self.show_all_checkbox = QCheckBox('Show all devices')
        self.show_all_checkbox.setChecked(False)
        self.show_all_checkbox.toggled.connect(self._filter_devices)
        options_layout.addWidget(self.show_all_checkbox)
        
        self.signal_filter_checkbox = QCheckBox('Strong signal only')
        self.signal_filter_checkbox.setChecked(True)
        self.signal_filter_checkbox.toggled.connect(self._filter_devices)
        options_layout.addWidget(self.signal_filter_checkbox)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Device list
        device_list_label = QLabel('Discovered Devices:')
        device_list_label.setStyleSheet('font-weight: bold; color: #ffffff;')
        layout.addWidget(device_list_label)
        
        self.device_list = QListWidget()
        self.device_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.device_list.itemSelectionChanged.connect(self._on_device_selection_changed)
        self.device_list.itemDoubleClicked.connect(self._on_device_double_clicked)
        layout.addWidget(self.device_list)
        
        # Connection controls
        connection_layout = QHBoxLayout()
        
        self.connect_button = QPushButton('📱 Connect to Selected Device')
        self.connect_button.setEnabled(False)
        self.connect_button.clicked.connect(self._connect_to_selected_device)
        connection_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton('❌ Disconnect')
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.clicked.connect(self._disconnect_device)
        connection_layout.addWidget(self.disconnect_button)
        
        layout.addLayout(connection_layout)
        
        # Status display
        status_label = QLabel('Connection Status:')
        status_label.setStyleSheet('font-weight: bold; color: #ffffff;')
        layout.addWidget(status_label)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        self.test_connection_button = QPushButton('🧪 Test Connection')
        self.test_connection_button.setEnabled(False)
        self.test_connection_button.clicked.connect(self._test_connection)
        button_layout.addWidget(self.test_connection_button)
        
        button_layout.addStretch()
        
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Set up Bluetooth manager callback
        if self.bt_manager:
            self.bt_manager.controller.set_connection_callback(self._on_connection_status_changed)
    
    def _setup_styling(self):
        """Apply styling to the dialog."""
        self.setStyleSheet('''
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 2px solid #606060;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #707070;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border-color: #404040;
            }
            QListWidget {
                background-color: #353535;
                border: 1px solid #606060;
                border-radius: 4px;
                color: #ffffff;
                selection-background-color: #0066cc;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #404040;
            }
            QListWidget::item:selected {
                background-color: #0066cc;
            }
            QTextEdit {
                background-color: #353535;
                border: 1px solid #606060;
                border-radius: 4px;
                color: #ffffff;
                font-family: monospace;
                font-size: 10px;
            }
            QProgressBar {
                border: 1px solid #606060;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 3px;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #606060;
                background-color: #353535;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #0066cc;
                background-color: #0066cc;
            }
        ''')
    
    def _show_bluetooth_unavailable(self):
        """Show message when Bluetooth is not available."""
        self._log_status("❌ Bluetooth functionality not available!")
        self._log_status("Install required package: pip install bleak")
        self.scan_button.setEnabled(False)
        self.connect_button.setEnabled(False)
    
    def _log_status(self, message: str):
        """Add a status message to the log."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        _LOGGER.info(f"Bluetooth Dialog: {message}")
    
    def _start_discovery(self):
        """Start enhanced Bluetooth device discovery."""
        if not self.bt_manager:
            return
        
        self._log_status("🔍 Starting enhanced Bluetooth discovery (3 attempts, 20s each)...")
        self.scan_button.setEnabled(False)
        self.quick_scan_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.device_list.clear()
        
        # Start enhanced discovery in background
        asyncio.create_task(self._discover_devices_enhanced())
    
    def _start_quick_discovery(self):
        """Start quick Bluetooth device discovery."""
        if not self.bt_manager:
            return
        
        self._log_status("⚡ Starting quick Bluetooth discovery (1 attempt, 10s)...")
        self.scan_button.setEnabled(False)
        self.quick_scan_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.device_list.clear()
        
        # Start quick discovery
        asyncio.create_task(self._discover_devices_quick())
    
    def _manual_device_entry(self):
        """Allow manual entry of device address."""
        from PyQt5.QtWidgets import QInputDialog
        
        address, ok = QInputDialog.getText(
            self, 
            'Manual Device Entry',
            'Enter Bluetooth MAC address (e.g., AA:BB:CC:DD:EE:FF):',
            text='00:00:00:00:00:00'
        )
        
        if ok and address:
            # Validate MAC address format
            import re
            if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', address):
                device_info = {
                    'address': address.upper(),
                    'name': f'Manual Entry - {address}',
                    'rssi': 0,
                    'manual_entry': True
                }
                self._add_device_to_list(device_info)
                self._log_status(f"✏️ Added manual device: {address}")
            else:
                self._log_status("❌ Invalid MAC address format")

    async def _discover_devices_enhanced(self):
        """Perform enhanced device discovery asynchronously."""
        try:
            devices = await self.bt_manager.discover_devices(timeout=20.0, max_attempts=3)
            
            self.progress_bar.setVisible(False)
            self.scan_button.setEnabled(True)
            self.quick_scan_button.setEnabled(True)
            
            if devices:
                self._log_status(f"✓ Enhanced discovery complete. Found {len(devices)} devices.")
                self._populate_device_list(devices)
            else:
                self._log_status("❌ No Bluetooth devices found with enhanced scan.")
                self._log_status("Try: 1) Move closer to Android TV, 2) Enable TV Bluetooth, 3) Manual entry")
                
        except Exception as exc:
            self.progress_bar.setVisible(False)
            self.scan_button.setEnabled(True)
            self.quick_scan_button.setEnabled(True)
            self._log_status(f"❌ Enhanced discovery failed: {str(exc)}")
            _LOGGER.error(f"Enhanced Bluetooth discovery error: {exc}")
    
    async def _discover_devices_quick(self):
        """Perform quick device discovery asynchronously."""
        try:
            devices = await self.bt_manager.discover_devices(timeout=10.0, max_attempts=1)
            
            self.progress_bar.setVisible(False)
            self.scan_button.setEnabled(True)
            self.quick_scan_button.setEnabled(True)
            
            if devices:
                self._log_status(f"⚡ Quick discovery complete. Found {len(devices)} devices.")
                self._populate_device_list(devices)
            else:
                self._log_status("❌ No devices found in quick scan. Try enhanced scan.")
                
        except Exception as exc:
            self.progress_bar.setVisible(False)
            self.scan_button.setEnabled(True)
            self.quick_scan_button.setEnabled(True)
            self._log_status(f"❌ Quick discovery failed: {str(exc)}")
            _LOGGER.error(f"Quick Bluetooth discovery error: {exc}")
    
    def _populate_device_list(self, devices: List[Dict[str, str]]):
        """Populate the device list with discovered devices."""
        self.device_list.clear()
        
        for device in devices:
            self._add_device_to_list(device)
        
        self._filter_devices()
    
    def _add_device_to_list(self, device: Dict[str, str]):
        """Add a single device to the list."""
        name = device.get('name', 'Unknown Device')
        address = device.get('address', '')
        rssi = device.get('rssi')
        
        # Create display text with enhanced info
        display_text = f"{name}"
        
        # Add signal strength info
        if rssi is not None:
            try:
                rssi_num = int(rssi) if isinstance(rssi, str) else rssi
                if rssi_num > -50:
                    signal_desc = "Excellent"
                elif rssi_num > -60:
                    signal_desc = "Very Good"
                elif rssi_num > -70:
                    signal_desc = "Good"
                elif rssi_num > -80:
                    signal_desc = "Fair"
                else:
                    signal_desc = "Weak"
                display_text += f" ({signal_desc}: {rssi_num} dBm)"
            except (ValueError, TypeError):
                display_text += f" (Signal: {rssi})"
        
        # Add manual entry indicator
        if device.get('manual_entry'):
            display_text = f"✏️ {display_text}"
        
        display_text += f"\n{address}"
        
        # Add discovery attempt info if available
        if device.get('discovery_attempt'):
            display_text += f" (Found in attempt {device.get('discovery_attempt')})"
        
        # Create list item
        item = QListWidgetItem(display_text)
        item.setData(0x0100, device)  # Use numeric constant instead of Qt.UserRole
        
        # Highlight likely Android TV devices
        if self._is_likely_android_tv(device):
            from PyQt5.QtGui import QColor
            item.setBackground(QColor(0, 0, 139))  # Dark blue
            item.setText(f"📺 {display_text}")
        
        # Color code by signal strength
        if rssi is not None:
            try:
                rssi_num = int(rssi) if isinstance(rssi, str) else rssi
                if rssi_num > -60:
                    from PyQt5.QtGui import QColor
                    item.setForeground(QColor(0, 255, 0))  # Green for strong signal
                elif rssi_num < -80:
                    from PyQt5.QtGui import QColor
                    item.setForeground(QColor(255, 165, 0))  # Orange for weak signal
            except (ValueError, TypeError):
                pass  # Skip coloring if RSSI is not numeric
        
        self.device_list.addItem(item)
    
    def _is_likely_android_tv(self, device: Dict[str, str]) -> bool:
        """Check if device is likely an Android TV."""
        name = device.get('name', '').lower()
        android_tv_indicators = [
            'android tv', 'google tv', 'chromecast', 'nvidia shield',
            'mi box', 'fire tv', 'roku', 'smart tv', 'tv box'
        ]
        return any(indicator in name for indicator in android_tv_indicators)
    
    def _filter_devices(self):
        """Filter device list based on checkboxes."""
        show_all = self.show_all_checkbox.isChecked()
        strong_signal_only = self.signal_filter_checkbox.isChecked()
        
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            device = item.data(0x0100)  # Use numeric constant
            
            should_show = True
            
            if not show_all:
                # Only show likely Android TV devices
                should_show = self._is_likely_android_tv(device)
            
            if strong_signal_only and should_show:
                # Filter by signal strength
                rssi = device.get('rssi')
                if rssi is not None:
                    try:
                        rssi_num = int(rssi) if isinstance(rssi, str) else rssi
                        should_show = rssi_num > -75  # Only show devices with decent signal
                    except (ValueError, TypeError):
                        should_show = True  # Show if we can't parse RSSI
            
            item.setHidden(not should_show)
    
    def _on_device_selection_changed(self):
        """Handle device selection change."""
        current_item = self.device_list.currentItem()
        if current_item:
            self.selected_device = current_item.data(Qt.UserRole)
            self.connect_button.setEnabled(True)
            
            device_name = self.selected_device.get('name', 'Unknown')
            self._log_status(f"📱 Selected: {device_name}")
        else:
            self.selected_device = None
            self.connect_button.setEnabled(False)
    
    def _on_device_double_clicked(self, item):
        """Handle double-click on device item."""
        self.selected_device = item.data(Qt.UserRole)
        self._connect_to_selected_device()
    
    def _connect_to_selected_device(self):
        """Connect to the selected Bluetooth device."""
        if not self.selected_device or not self.bt_manager:
            return
        
        device_name = self.selected_device.get('name', 'Unknown Device')
        device_address = self.selected_device.get('address', '')
        
        self._log_status(f"🔗 Connecting to {device_name}...")
        self.connect_button.setEnabled(False)
        self.scan_button.setEnabled(False)
        
        # Start connection in background
        asyncio.create_task(self._connect_device(device_address))
    
    async def _connect_device(self, device_address: str):
        """Perform device connection asynchronously with retry logic."""
        if not self.bt_manager:
            self._log_status("❌ Bluetooth manager not available")
            return
            
        try:
            success = await self.bt_manager.connect_with_retry(device_address, max_retries=3)
            
            if success:
                device_info = None
                if self.bt_manager.controller:
                    device_info = self.bt_manager.controller.get_device_info()
                
                if device_info:
                    self._log_status(f"✅ Connected to {device_info['name']}")
                else:
                    self._log_status(f"✅ Connected to {device_address}")
                
                self.disconnect_button.setEnabled(True)
                self.test_connection_button.setEnabled(True)
                
                # Start connection monitoring
                self.connection_timer.start(5000)  # Check every 5 seconds
                
                # Emit signal for main application
                if device_info:
                    self.device_connected.emit(device_info)
                else:
                    # Fallback device info
                    fallback_info = {'name': 'Connected Device', 'address': device_address}
                    self.device_connected.emit(fallback_info)
                
            else:
                attempts = self.bt_manager.get_connection_history(device_address)
                self._log_status(f"❌ Connection failed after {attempts} attempts")
                self.connect_button.setEnabled(True)
                self.scan_button.setEnabled(True)
                
        except Exception as exc:
            self._log_status(f"❌ Connection error: {str(exc)}")
            self.connect_button.setEnabled(True)
            self.scan_button.setEnabled(True)
            _LOGGER.error(f"Bluetooth connection error: {exc}")
    
    def _disconnect_device(self):
        """Disconnect from current device."""
        if not self.bt_manager:
            return
        
        self._log_status("🔌 Disconnecting...")
        asyncio.create_task(self._perform_disconnect())
    
    async def _perform_disconnect(self):
        """Perform disconnection asynchronously."""
        try:
            await self.bt_manager.disconnect()
            self._log_status("✅ Disconnected")
            
            self.disconnect_button.setEnabled(False)
            self.test_connection_button.setEnabled(False)
            self.connect_button.setEnabled(True)
            self.scan_button.setEnabled(True)
            
            self.connection_timer.stop()
            
        except Exception as exc:
            self._log_status(f"❌ Disconnect error: {str(exc)}")
            _LOGGER.error(f"Bluetooth disconnect error: {exc}")
    
    def _test_connection(self):
        """Test the current Bluetooth connection."""
        if not self.bt_manager or not self.bt_manager.is_connected():
            self._log_status("❌ Not connected to test")
            return
        
        self._log_status("🧪 Testing connection by sending volume up command...")
        asyncio.create_task(self._perform_connection_test())
    
    async def _perform_connection_test(self):
        """Perform connection test asynchronously."""
        try:
            success = await self.bt_manager.controller.volume_up()
            if success:
                self._log_status("✅ Test successful - volume up command sent")
            else:
                self._log_status("❌ Test failed - could not send command")
                
        except Exception as exc:
            self._log_status(f"❌ Test error: {str(exc)}")
            _LOGGER.error(f"Bluetooth test error: {exc}")
    
    def _check_connection_status(self):
        """Periodically check connection status."""
        if self.bt_manager and not self.bt_manager.is_connected():
            self._log_status("⚠️ Connection lost")
            self.disconnect_button.setEnabled(False)
            self.test_connection_button.setEnabled(False)
            self.connect_button.setEnabled(True)
            self.connection_timer.stop()
    
    def _on_connection_status_changed(self, connected: bool, message: str):
        """Handle connection status changes from Bluetooth manager."""
        if connected:
            self._log_status(f"✅ {message}")
        else:
            self._log_status(f"❌ {message}")
    
    def closeEvent(self, a0):
        """Handle dialog close event."""
        # Stop any ongoing operations
        if self.connection_timer.isActive():
            self.connection_timer.stop()
        
        super().closeEvent(a0)
    
    def get_connected_device_info(self) -> Optional[Dict[str, str]]:
        """Get information about the currently connected device."""
        if self.bt_manager and self.bt_manager.is_connected():
            return self.bt_manager.get_connected_device_info()
        return None