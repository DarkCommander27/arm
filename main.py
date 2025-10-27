import asyncio
import functools
import logging
import sys
from pathlib import Path

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QScrollArea,
)
from qasync import QEventLoop, asyncSlot

import history
from bluetooth_dialog import BluetoothPairingDialog
from bluetooth_control import BluetoothDeviceManager, BLUETOOTH_AVAILABLE

_LOGGER = logging.getLogger(__name__)


class FavoritesDialog(QDialog):
    """Dialog for managing favorite apps."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Manage Quick Apps')
        self.setFixedSize(300, 300)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # App list with checkboxes
        self.app_checks = {}
        apps = [
            ('Netflix', 'netflix'),
            ('YouTube', 'youtube'),
            ('Prime Video', 'prime'),
            ('Plex', 'plex'),
            ('Settings', 'settings'),
            ('HBO Max', 'hbo'),
            ('Disney+', 'disney'),
            ('Hulu', 'hulu'),
        ]
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        for app_name, app_key in apps:
            checkbox = QCheckBox(app_name)
            checkbox.setStyleSheet('font-size: 12px;')
            self.app_checks[app_key] = (checkbox, app_name)
            scroll_layout.addWidget(checkbox)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton('OK')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_selected_apps(self):
        """Get list of selected apps."""
        selected = []
        for key, (checkbox, name) in self.app_checks.items():
            if checkbox.isChecked():
                selected.append((name, key))
        return selected


def connection_check(func):
    @functools.wraps(func)
    def wrapper(self):
        try:
            if self.bluetooth_connected:
                return func(self)
            # Show message to connect via Bluetooth
            self.search_label.setText('Not connected - use Bluetooth button')
        except Exception as exc:
            _LOGGER.error('Error: %s', exc)
            self.search_label.setText('Error')
            return None

    return wrapper


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        Path('keys').mkdir(parents=True, exist_ok=True)

        # Bluetooth functionality
        self.bluetooth_manager = BluetoothDeviceManager() if BLUETOOTH_AVAILABLE else None
        self.bluetooth_connected = False

        self._main_window_configure()
        self._create_tray()

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 0, 20, 0)

        self.search_label = QLabel('Not connected')
        top_layout.addWidget(self.search_label)

        # Bluetooth connection button
        self.bluetooth_btn = QPushButton('📡 Connect via Bluetooth')
        self.bluetooth_btn.setFixedSize(220, 40)
        self.bluetooth_btn.setToolTip('Bluetooth pairing with Android TV')
        self.bluetooth_btn.clicked.connect(self._on_bluetooth_pairing)
        if not BLUETOOTH_AVAILABLE:
            self.bluetooth_btn.setEnabled(False)
            self.bluetooth_btn.setToolTip('Bluetooth not available (install bleak package)')
        top_layout.addWidget(self.bluetooth_btn)

        # Manage favorites button
        manage_fav_btn = QPushButton('⭐')
        manage_fav_btn.setFixedSize(40, 40)
        manage_fav_btn.setToolTip('Manage quick apps')
        manage_fav_btn.clicked.connect(self._on_manage_favorites)
        top_layout.addWidget(manage_fav_btn)

        # Favorite apps grid layout for quick access
        self.favorite_apps_layout = QGridLayout()
        self.favorite_apps_layout.setSpacing(3)
        self.favorite_apps = {}  # Dictionary to store favorite app buttons
        
        # History list (previously connected devices)
        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        self.history_list.setMinimumHeight(60)
        self.history_list.setMaximumHeight(80)

        self._refresh_device_lists()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)  # Further reduced margins
        main_layout.setSpacing(3)  # Further reduced spacing

        main_layout.addLayout(top_layout)

        # Section: Quick Launch
        apps_label = QLabel('Quick Apps')
        apps_label.setStyleSheet('font-weight: bold; font-size: 11px; color: #87CEEB;')
        main_layout.addWidget(apps_label)
        main_layout.addLayout(self.favorite_apps_layout)

        # Section: Recently Connected
        history_label = QLabel('Recently Connected')
        history_label.setStyleSheet('font-weight: bold; font-size: 10px; color: #90EE90;')
        main_layout.addWidget(history_label)
        main_layout.addWidget(self.history_list)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(3)  # Reduced spacing
        grid_layout.setVerticalSpacing(3)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Remote Control buttons
        self.add_button(grid_layout, 'Power', 0, 0, self._on_power, size=QSize(60, 40))
        self.add_button(grid_layout, 'Back', 0, 1, self._on_back, size=QSize(60, 40))
        self.add_button(grid_layout, 'Menu', 0, 2, self._on_menu, size=QSize(60, 40))

        self.add_button(grid_layout, 'CH▲', 1, 0, self._on_channel_up, size=QSize(60, 40))
        self.add_button(grid_layout, 'Home', 1, 1, self._on_home, size=QSize(60, 40))
        self.add_button(grid_layout, 'VOL+', 1, 2, self._on_volume_up, size=QSize(60, 40))

        self.add_button(grid_layout, 'CH▼', 2, 0, self._on_channel_down, size=QSize(60, 40))
        self.add_button(grid_layout, 'Mute', 2, 1, self._on_mute, size=QSize(60, 40))
        self.add_button(grid_layout, 'VOL-', 2, 2, self._on_volume_down, size=QSize(60, 40))

        navigation_layout = QGridLayout()
        navigation_layout.setHorizontalSpacing(3)  # Reduced spacing
        navigation_layout.setVerticalSpacing(3)
        navigation_layout.setContentsMargins(0, 0, 0, 0)

        # D-Pad navigation
        self.add_button(navigation_layout, '▲', 0, 1, self._on_dpad_up, size=QSize(40, 40))
        self.add_button(navigation_layout, '◀', 1, 0, self._on_dpad_left, size=QSize(40, 40))
        self.add_button(navigation_layout, 'OK', 1, 1, self._on_dpad_center, size=QSize(40, 40))
        self.add_button(navigation_layout, '▶', 1, 2, self._on_dpad_right, size=QSize(40, 40))
        self.add_button(navigation_layout, '▼', 2, 1, self._on_dpad_down, size=QSize(40, 40))

        main_layout.addLayout(grid_layout)
        main_layout.addLayout(navigation_layout)
        self.setLayout(main_layout)
        # Ensure the window is shown after layout setup
        self.show()

        # Apply a modern dark style to the main window and buttons
        self.setStyleSheet('''
            QWidget {
                background-color: #23272e;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #444b58;
                color: #e0e0e0;
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #6b46c1;
                border-radius: 8px;
                padding: 4px 8px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
                border-color: #8b5cf6;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #5b21b6;
                border-color: #6b46c1;
            }
            QListWidget {
                background-color: #2c313c;
                border: 1px solid #6b46c1;
                color: #e0e0e0;
                font-size: 14px;
                selection-background-color: #7c3aed;
            }
            QListWidget::item:selected {
                background-color: #7c3aed;
                color: #ffffff;
            }
            QLabel {
                font-size: 14px;
                color: #e0e0e0;
            }
        ''')

    def _main_window_configure(self):
        """Configure the main window properties."""
        self.setWindowTitle('Android TV Remote Control')
        # Compact window sized for remote control
        self.setFixedSize(520, 700)
        self.setWindowIcon(QIcon('resources/icon32.ico'))

    def add_button(self, layout, label, row, col, handler, size=None):
        if size is None:
            size = QSize(80, 60)
        btn = QPushButton(label)
        btn.setFixedSize(size)
        btn.clicked.connect(handler)
        layout.addWidget(btn, row, col)

    def _on_tray_icon_activated(self, reason: int) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self._show()

    def _show(self) -> None:
        self.show()
        self.activateWindow()

    def _exit_app(self) -> None:
        self.tray_icon.hide()
        try:
            if self.bluetooth_connected and self.bluetooth_manager:
                asyncio.create_task(self.bluetooth_manager.disconnect())
        except Exception as exc:
            _LOGGER.error('Disconnect Error: %s', exc)
        app = QApplication.instance()
        if app:
            app.quit()

    def _create_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('resources/icon32.ico'))

        tray_menu = QMenu()

        open_action = QAction('Open', self)
        open_action.triggered.connect(self._show)
        tray_menu.addAction(open_action)

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self._exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self._on_tray_icon_activated)

    @connection_check
    def _on_power(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.power())

    @connection_check
    def _on_back(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.back())

    @connection_check
    def _on_menu(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.menu())

    @connection_check
    def _on_home(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.home())

    @connection_check
    def _on_channel_up(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.channel_up())

    @connection_check
    def _on_channel_down(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.channel_down())

    @connection_check
    def _on_volume_up(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.volume_up())

    @connection_check
    def _on_volume_down(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.volume_down())

    @connection_check
    def _on_mute(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.volume_mute())

    @connection_check
    def _on_dpad_up(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.dpad_up())

    @connection_check
    def _on_dpad_down(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.dpad_down())

    @connection_check
    def _on_dpad_left(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.dpad_left())

    @connection_check
    def _on_dpad_right(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.dpad_right())

    @connection_check
    def _on_dpad_center(self) -> None:
        if self.bluetooth_manager:
            asyncio.create_task(self.bluetooth_manager.controller.dpad_center())

    def _on_bluetooth_pairing(self):
        """Open Bluetooth pairing dialog."""
        if not BLUETOOTH_AVAILABLE:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                'Bluetooth Not Available',
                'Bluetooth functionality is not available.\n\n'
                'To enable Bluetooth support, install the required package:\n'
                'pip install bleak'
            )
            return
        
        dialog = BluetoothPairingDialog(self)
        dialog.device_connected.connect(self._on_bluetooth_device_connected)
        dialog.exec_()

    def _on_manage_favorites(self):
        """Open dialog to manage favorite apps."""
        dialog = FavoritesDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected = dialog.get_selected_apps()
            self._update_favorite_apps(selected)
    
    def _update_favorite_apps(self, selected_apps):
        """Update the displayed favorite apps based on user selection."""
        # Clear existing buttons
        while self.favorite_apps_layout.count():
            child = self.favorite_apps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.favorite_apps.clear()
        
        # Create buttons for selected apps
        for idx, (app_name, app_key) in enumerate(selected_apps):
            btn = QPushButton(app_name)
            btn.setFixedSize(75, 35)
            btn.setStyleSheet('font-size: 10px;')
            btn.clicked.connect(lambda checked, key=app_key: self._launch_app(key))
            row = idx // 3
            col = idx % 3
            self.favorite_apps_layout.addWidget(btn, row, col)
            self.favorite_apps[app_key] = btn
    
    def _launch_app(self, app_key):
        """Launch an app by sending appropriate keycode."""
        try:
            if not self.bluetooth_connected:
                self.search_label.setText('Not connected - use Bluetooth button')
                return
            
            if self.bluetooth_manager:
                # For Bluetooth HID, we can't directly launch apps
                # So we just send HOME to get to the launcher
                asyncio.create_task(self._launch_app_bluetooth(app_key))
        except Exception as exc:
            _LOGGER.error('Launch app error: %s', exc)
            self.search_label.setText('Error launching app')
    
    async def _launch_app_bluetooth(self, app_key):
        """Launch app via Bluetooth by sending HOME command."""
        try:
            # For Bluetooth HID, we can't directly launch apps
            # So we just send HOME to get to the launcher
            await self.bluetooth_manager.controller.home()
            self.search_label.setText(f'Sent HOME - navigate to {app_key} manually')
        except Exception as exc:
            _LOGGER.error(f'Bluetooth app launch error: {exc}')
            self.search_label.setText('Error with Bluetooth command')

    def _refresh_device_lists(self):
        """Refresh history list and favorite apps."""
        self.history_list.clear()
        for entry in history.get_history():
            label = f"{entry['device_name']} ({entry['ip']})"
            item = QListWidgetItem(label)
            item.setData(1000, entry)
            self.history_list.addItem(item)
        
        # Create favorite app buttons for quick launching
        self._refresh_favorite_apps()

    def _refresh_favorite_apps(self):
        """Create quick-launch buttons for default apps."""
        # Clear existing buttons
        while self.favorite_apps_layout.count():
            child = self.favorite_apps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.favorite_apps.clear()
        
        # Default favorite apps
        default_apps = [
            ('Netflix', 'netflix'),
            ('YouTube', 'youtube'),
            ('Prime', 'prime'),
        ]
        
        for idx, (app_name, app_key) in enumerate(default_apps):
            btn = QPushButton(app_name)
            btn.setFixedSize(75, 35)
            btn.setStyleSheet('font-size: 10px;')
            btn.clicked.connect(lambda checked, key=app_key: self._launch_app(key))
            row = idx // 3
            col = idx % 3
            self.favorite_apps_layout.addWidget(btn, row, col)
            self.favorite_apps[app_key] = btn

    def _on_bluetooth_device_connected(self, device_info):
        """Handle successful Bluetooth device connection."""
        _LOGGER.info(f"Bluetooth device connected: {device_info}")
        
        # Update UI
        self.bluetooth_connected = True
        self.search_label.setText(f"🔵 BT: {device_info.get('name', 'Unknown')}")
        
        # Add to history (with a special Bluetooth indicator)
        device_name = f"[BT] {device_info.get('name', 'Bluetooth Device')}"
        device_address = device_info.get('address', 'Unknown')
        history.update_history(device_name, device_address, False)
        self._refresh_device_lists()
        
        _LOGGER.info(f"Successfully connected via Bluetooth to {device_info.get('name')}")

    def _on_history_item_double_clicked(self, item):
        """Handle double-click on history item - try to reconnect to Bluetooth device."""
        entry = item.data(1000)
        if entry and entry.get('device_name', '').startswith('[BT]'):
            # This is a Bluetooth device, open Bluetooth dialog for reconnection
            self._on_bluetooth_pairing()
        else:
            # Legacy entry, show message
            self.search_label.setText('Use Bluetooth button to connect')


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s,%(msecs)d %(levelname)s %(name)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler(sys.stdout),
        ],
    )

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    app.setWindowIcon(QIcon('resources/icon32.ico'))

    window = MainWindow()
    window.show()

    with loop:
        sys.exit(loop.run_forever())
