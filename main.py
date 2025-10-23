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
)
from qasync import QEventLoop

from remote_control import RemoteControl
import history

_LOGGER = logging.getLogger(__name__)


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

        # Favorites and History lists
        self.favorites_list = QListWidget()
        self.favorites_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.favorites_list.itemDoubleClicked.connect(self._on_favorite_item_double_clicked)
        self.favorites_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.favorites_list.customContextMenuRequested.connect(self._show_history_context_menu)
        self.favorites_list.currentItemChanged.connect(self._on_favorite_selection_changed)
        self.favorites_list.setMinimumHeight(60)
        self.favorites_list.setMaximumHeight(80)

        # Favorite apps grid layout for quick access
        self.favorite_apps_layout = QGridLayout()
        self.favorite_apps_layout.setSpacing(5)
        self.favorite_apps = {}  # Dictionary to store favorite app buttons

        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        self.history_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._show_history_context_menu)
        self.history_list.currentItemChanged.connect(self._on_history_selection_changed)
        self.history_list.setMinimumHeight(80)
        self.history_list.setMaximumHeight(120)

        self._refresh_device_lists()

        # Button to toggle favorite
        self.favorite_button = QPushButton('Toggle Favorite')
        self.favorite_button.setFixedSize(160, 45)
        self.favorite_button.clicked.connect(self._on_toggle_favorite)
        self.favorite_button.setEnabled(False)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # Further reduced margins
        main_layout.setSpacing(6)  # Further reduced spacing

        main_layout.addLayout(top_layout)

        # Section: Favorite Devices (quick access)
        devices_label = QLabel('Favorite Devices')
        devices_label.setStyleSheet('font-weight: bold; font-size: 14px; color: #FFD700;')
        main_layout.addWidget(devices_label)
        main_layout.addWidget(self.favorites_list)

        # Section: Quick App Launchers
        apps_label = QLabel('Quick App Launchers')
        apps_label.setStyleSheet('font-weight: bold; font-size: 14px; color: #87CEEB;')
        main_layout.addWidget(apps_label)
        main_layout.addLayout(self.favorite_apps_layout)

        # Section: History
        history_label = QLabel('History')
        history_label.setStyleSheet('font-weight: bold; font-size: 12px; color: #90EE90;')
        main_layout.addWidget(history_label)
        main_layout.addWidget(self.history_list)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(4)  # Reduced spacing further
        grid_layout.setVerticalSpacing(4)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Remote Control buttons
        self.add_button(grid_layout, 'Power', 0, 0, self._on_power, size=QSize(70, 50))
        self.add_button(grid_layout, 'Back', 0, 1, self._on_back, size=QSize(70, 50))
        self.add_button(grid_layout, 'Menu', 0, 2, self._on_menu, size=QSize(70, 50))

        self.add_button(grid_layout, 'CH▲', 1, 0, self._on_channel_up, size=QSize(70, 50))
        self.add_button(grid_layout, 'Home', 1, 1, self._on_home, size=QSize(70, 50))
        self.add_button(grid_layout, 'VOL+', 1, 2, self._on_volume_up, size=QSize(70, 50))

        self.add_button(grid_layout, 'CH▼', 2, 0, self._on_channel_down, size=QSize(70, 50))
        self.add_button(grid_layout, 'Mute', 2, 1, self._on_mute, size=QSize(70, 50))
        self.add_button(grid_layout, 'VOL-', 2, 2, self._on_volume_down, size=QSize(70, 50))

        navigation_layout = QGridLayout()
        navigation_layout.setHorizontalSpacing(4)  # Reduced spacing
        navigation_layout.setVerticalSpacing(4)
        navigation_layout.setContentsMargins(0, 0, 0, 0)

        # D-Pad navigation
        self.add_button(navigation_layout, '▲', 0, 1, self._on_dpad_up, size=QSize(50, 50))
        self.add_button(navigation_layout, '◀', 1, 0, self._on_dpad_left, size=QSize(50, 50))
        self.add_button(navigation_layout, 'OK', 1, 1, self._on_dpad_center, size=QSize(50, 50))
        self.add_button(navigation_layout, '▶', 1, 2, self._on_dpad_right, size=QSize(50, 50))
        self.add_button(navigation_layout, '▼', 2, 1, self._on_dpad_down, size=QSize(50, 50))

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
        # Increased window height to accommodate all buttons and favorites
        self.setFixedSize(600, 1050)
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
        self.search_label.setText('Searching...')
        if self.is_connected:
            self.is_connected = False
            try:
                self.remote_control.disconnect()
            except Exception:
                pass

        try:
            addrs: list = await self.remote_control.find_android_tv()
            if len(addrs) > 0:
                self.search_label.setText(f'Found TV at {addrs[0]}')

                try:
                    def get_pairing_code():
                        code, ok = QInputDialog.getText(self, 'TV Remote Control', 'Enter the pairing code displayed on your TV:')
                        if ok and code.strip():
                            return (code.strip(), True)
                        return ('', False)
                    
                    await self.remote_control.pair(addrs[0], get_pairing_code)
                    device_info = self.remote_control.device_info()
                except asyncio.TimeoutError:
                    self.search_label.setText('Pairing timeout - try again')
                    _LOGGER.error('Pairing timeout')
                    return
                except Exception as exc:
                    self.search_label.setText('Pairing failed')
                    _LOGGER.error('Pair Error: %s', exc)
                    return

                if device_info:
                    self.search_label.setText(f"✓ {device_info['manufacturer']} {device_info['model']}")
                    self.is_connected = True
                    # Add newly paired device to history
                    device_name = f"{device_info.get('manufacturer', 'Unknown')} {device_info.get('model', 'Device')}"
                    history.update_history(device_name, addrs[0], False)
                    self._refresh_device_lists()
            else:
                self.search_label.setText('No TV found - check network')
        except Exception as exc:
            self.search_label.setText('Connection error')
            _LOGGER.error('Search Error: %s', exc)

    def _on_pair_new_device(self):
        """Handler for the 'Pair New Device' button."""
        asyncio.create_task(self._pair())

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
        self.favorite_button.setEnabled(current is not None)

    def _on_history_selection_changed(self, current, previous):
        """Handle selection change in history list."""
        self.favorite_button.setEnabled(current is not None)

    def _on_toggle_favorite(self):
        """Toggle favorite status of selected device."""
        # Toggle favorite for selected item in either list
        item = self.favorites_list.currentItem() or self.history_list.currentItem()
        if not item:
            return
        entry = item.data(1000)
        new_fav = not entry.get('favorite', False)
        history.set_favorite(entry['ip'], new_fav)
        self._refresh_device_lists()

    def _refresh_device_lists(self):
        """Refresh both favorites and history lists."""
        self.favorites_list.clear()
        self.history_list.clear()
        for entry in history.get_favorites():
            label = f"★ {entry['device_name']} ({entry['ip']})"
            item = QListWidgetItem(label)
            item.setData(1000, entry)
            self.favorites_list.addItem(item)
        for entry in history.get_history():
            if not entry.get('favorite'):
                label = f"{entry['device_name']} ({entry['ip']})"
                item = QListWidgetItem(label)
                item.setData(1000, entry)
                self.history_list.addItem(item)
        
        # Create favorite app buttons for quick launching
        self._refresh_favorite_apps()

    def _refresh_favorite_apps(self):
        """Create quick-launch buttons for common apps."""
        # Clear existing buttons
        while self.favorite_apps_layout.count():
            child = self.favorite_apps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.favorite_apps.clear()
        
        # Common app shortcuts
        common_apps = [
            ('Netflix', self._launch_netflix),
            ('YouTube', self._launch_youtube),
            ('Prime', self._launch_prime),
            ('Plex', self._launch_plex),
            ('Settings', self._launch_settings),
        ]
        
        for idx, (app_name, handler) in enumerate(common_apps):
            btn = QPushButton(app_name)
            btn.setFixedSize(90, 45)
            btn.clicked.connect(handler)
            row = idx // 3
            col = idx % 3
            self.favorite_apps_layout.addWidget(btn, row, col)
    
    @connection_check
    def _launch_netflix(self):
        """Launch Netflix app."""
        self.remote_control.send_key('KEYCODE_COMPONENT1')
        
    @connection_check
    def _launch_youtube(self):
        """Launch YouTube app."""
        self.remote_control.send_key('KEYCODE_COMPONENT2')
        
    @connection_check
    def _launch_prime(self):
        """Launch Prime Video app."""
        self.remote_control.send_key('KEYCODE_COMPONENT3')
        
    @connection_check
    def _launch_plex(self):
        """Launch Plex app."""
        self.remote_control.send_key('KEYCODE_COMPONENT4')
        
    @connection_check
    def _launch_settings(self):
        """Launch Settings app."""
        self.remote_control.send_key('KEYCODE_SETTINGS')

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
