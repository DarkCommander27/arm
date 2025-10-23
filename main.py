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
from qasync import QEventLoop

from remote_control import RemoteControl
import history

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
            if self.is_connected:
                return func(self)
            self._on_search()
        except Exception as exc:
            _LOGGER.error('Error: %s', exc)
            self.search_label.setText('Error')
            return None

    return wrapper


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        Path('keys').mkdir(parents=True, exist_ok=True)

        self.is_connected = False
        self.remote_control = RemoteControl()

        self._main_window_configure()
        self._create_tray()

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 0, 20, 0)

        self.search_label = QLabel('Not connected')
        top_layout.addWidget(self.search_label)

        # Add 'Pair New Device' button
        pair_button = QPushButton('Pair New Device')
        pair_button.setFixedSize(180, 40)
        pair_button.clicked.connect(self._on_pair_new_device)
        top_layout.addWidget(pair_button)

        # Keep the search/refresh button for rescanning
        search_button = QPushButton('⟲')
        search_button.setFixedSize(40, 40)
        search_button.setToolTip('Rescan for devices')
        search_button.clicked.connect(self._on_search)
        top_layout.addWidget(search_button)

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
            self.remote_control.disconnect()
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
        self.remote_control.power()

    @connection_check
    def _on_back(self) -> None:
        self.remote_control.back()

    @connection_check
    def _on_menu(self) -> None:
        self.remote_control.menu()

    @connection_check
    def _on_home(self) -> None:
        self.remote_control.home()

    @connection_check
    def _on_channel_up(self) -> None:
        self.remote_control.channel_up()

    @connection_check
    def _on_channel_down(self) -> None:
        self.remote_control.channel_down()

    @connection_check
    def _on_volume_up(self) -> None:
        self.remote_control.volume_up()

    @connection_check
    def _on_volume_down(self) -> None:
        self.remote_control.volume_down()

    @connection_check
    def _on_mute(self) -> None:
        self.remote_control.volume_mute()

    @connection_check
    def _on_dpad_up(self) -> None:
        self.remote_control.dpad_up()

    @connection_check
    def _on_dpad_down(self) -> None:
        self.remote_control.dpad_down()

    @connection_check
    def _on_dpad_left(self) -> None:
        self.remote_control.dpad_left()

    @connection_check
    def _on_dpad_right(self) -> None:
        self.remote_control.dpad_right()

    @connection_check
    def _on_dpad_center(self) -> None:
        self.remote_control.dpad_center()

    def _on_search(self) -> None:
        asyncio.create_task(self._pair())

    async def _pair(self) -> None:
        self.search_label.setText('Scanning...')
        if self.is_connected:
            self.is_connected = False
            try:
                self.remote_control.disconnect()
            except Exception:
                pass

        try:
            addrs: list = await asyncio.wait_for(self.remote_control.find_android_tv(), timeout=10)
            if len(addrs) > 0:
                tv_addr = addrs[0]
                self.search_label.setText(f'Pairing {tv_addr}...')
                _LOGGER.info('Found TV at %s', tv_addr)

                try:
                    def get_pairing_code():
                        code, ok = QInputDialog.getText(
                            self, 
                            'Pairing Code', 
                            'Enter code from TV screen:',
                            QInputDialog.Normal,
                            ''
                        )
                        if ok and code.strip():
                            return (code.strip(), True)
                        return ('', False)
                    
                    # Try to pair with timeout
                    await asyncio.wait_for(
                        self.remote_control.pair(tv_addr, get_pairing_code),
                        timeout=30
                    )
                    
                    device_info = self.remote_control.device_info()
                    if device_info:
                        self.search_label.setText(f"✓ {device_info['manufacturer']}")
                        self.is_connected = True
                        device_name = f"{device_info.get('manufacturer', 'TV')} {device_info.get('model', '')}"
                        history.update_history(device_name, tv_addr, False)
                        self._refresh_device_lists()
                        _LOGGER.info('Successfully paired with %s', tv_addr)
                    else:
                        self.search_label.setText('Pairing failed')
                        
                except asyncio.TimeoutError:
                    self.search_label.setText('Pairing timeout')
                    _LOGGER.error('Pairing timeout for %s', tv_addr)
                except Exception as exc:
                    self.search_label.setText('Pairing error')
                    _LOGGER.error('Pairing error: %s', exc)
            else:
                self.search_label.setText('No TV found')
                _LOGGER.warning('No Android TV found on network')
                
        except asyncio.TimeoutError:
            self.search_label.setText('Search timeout')
            _LOGGER.error('Search timeout')
        except Exception as exc:
            self.search_label.setText('Search error')
            _LOGGER.error('Search error: %s', exc)

    def _on_pair_new_device(self):
        """Handler for the 'Pair New Device' button."""
        asyncio.create_task(self._pair())
    
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
            if not self.is_connected:
                self.search_label.setText('Not connected - pair first')
                return
            
            # App launch keycodes
            app_codes = {
                'netflix': 'KEYCODE_NETFLIX',
                'youtube': 'KEYCODE_YOUTUBE',
                'prime': 'KEYCODE_PRIME_VIDEO',
                'plex': 'KEYCODE_PLEX',
                'settings': 'KEYCODE_SETTINGS',
                'hbo': 'KEYCODE_HBO',
                'disney': 'KEYCODE_DISNEY',
                'hulu': 'KEYCODE_HULU',
            }
            
            if app_key in app_codes:
                self.remote_control.send_key_command(app_codes[app_key])
                self.search_label.setText(f'Launching {app_key}...')
        except Exception as exc:
            _LOGGER.error('Launch app error: %s', exc)
            self.search_label.setText('Error launching app')

    def _show_history_context_menu(self, position):
        """Show context menu for history items."""
        # This method can be expanded later for right-click context menu
        pass

    def _on_favorite_item_double_clicked(self, item):
        """Handle double-click on favorite item."""
        entry = item.data(1000)
        asyncio.create_task(self._connect_to_history_device(entry))

    def _on_history_item_double_clicked(self, item):
        """Handle double-click on history item."""
        entry = item.data(1000)
        asyncio.create_task(self._connect_to_history_device(entry))

    def _on_favorite_selection_changed(self, current, previous):
        """Handle selection change in favorites list."""
        pass

    def _on_history_selection_changed(self, current, previous):
        """Handle selection change in history list."""
        pass

    def _on_toggle_favorite(self):
        """Toggle favorite status of selected device."""
        pass

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

    async def _connect_to_history_device(self, entry):
        """Connect to a device from history or favorites."""
        self.search_label.setText(f"Connecting to {entry['device_name']}...")
        try:
            def get_pairing_code():
                code, ok = QInputDialog.getText(self, 'TV Remote Control', 'Enter the pairing code displayed on your TV:')
                if ok and code.strip():
                    return (code.strip(), True)
                return ('', False)
            
            await self.remote_control.pair(entry['ip'], get_pairing_code)
            device_info = self.remote_control.device_info()
            if device_info:
                self.search_label.setText(f"{device_info['manufacturer']} {device_info['model']}")
                self.is_connected = True
                # Update history with latest connection
                history.update_history(entry['device_name'], entry['ip'], entry.get('favorite', False))
                self._refresh_device_lists()
        except Exception as exc:
            self.search_label.setText('Not connected')
            _LOGGER.error('History Connect Error: %s', exc)


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
