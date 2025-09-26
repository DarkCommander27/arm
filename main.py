import asyncio
import functools
import logging
import sys
from pathlib import Path
from typing import Callable

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
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

        search_button = QPushButton('⟲')
        search_button.setFixedSize(32, 32)
        search_button.clicked.connect(self._on_search)
        top_layout.addWidget(search_button)

        # Connection history list

        self.history_list = QListWidget()
        self.history_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        self._refresh_history_list()

        # Button to toggle favorite
        self.favorite_button = QPushButton('Toggle Favorite')
        self.favorite_button.setFixedSize(120, 32)
        self.favorite_button.clicked.connect(self._on_toggle_favorite)
        self.favorite_button.setEnabled(False)
        self.history_list.currentItemChanged.connect(self._on_history_selection_changed)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(QLabel('Connection History / Quick Access:'))
        main_layout.addWidget(self.history_list)
        main_layout.addWidget(self.favorite_button)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        grid_layout.setVerticalSpacing(15)

        self.add_button(grid_layout, 'Power', 0, 0, self._on_power)
        self.add_button(grid_layout, 'Back', 0, 1, self._on_back)
        self.add_button(grid_layout, 'Menu', 0, 2, self._on_menu)

        self.add_button(grid_layout, 'CH▲', 1, 0, self._on_channel_up)
        self.add_button(grid_layout, 'Home', 1, 1, self._on_home)
        self.add_button(grid_layout, 'VOL+', 1, 2, self._on_volume_up)

        self.add_button(grid_layout, 'CH▼', 2, 0, self._on_channel_down)
        self.add_button(grid_layout, 'Mute', 2, 1, self._on_mute)
        self.add_button(grid_layout, 'VOL-', 2, 2, self._on_volume_down)

        navigation_layout = QGridLayout()
        navigation_layout.setHorizontalSpacing(10)

        self.add_button(navigation_layout, '▲', 0, 1, self._on_dpad_up)
        self.add_button(navigation_layout, '◀', 1, 0, self._on_dpad_left)
        self.add_button(navigation_layout, 'OK', 1, 1, self._on_dpad_center)
        self.add_button(navigation_layout, '▶', 1, 2, self._on_dpad_right)
        self.add_button(navigation_layout, '▼', 2, 1, self._on_dpad_down)

        main_layout.addLayout(grid_layout)
        main_layout.addLayout(navigation_layout)
        self.setLayout(main_layout)
        # Ensure the window is shown after layout setup
        self.show()

    def _on_history_selection_changed(self, current, previous):
        self.favorite_button.setEnabled(current is not None)

    def _on_toggle_favorite(self):
        item = self.history_list.currentItem()
        if not item:
            return
        entry = item.data(1000)
        new_fav = not entry.get('favorite', False)
        history.set_favorite(entry['ip'], new_fav)
        self._refresh_history_list()

    def _refresh_history_list(self):
        self.history_list.clear()
        for entry in history.get_history():
            label = f"{'★ ' if entry.get('favorite') else ''}{entry['device_name']} ({entry['ip']})"
            item = QListWidgetItem(label)
            item.setData(1000, entry)  # Custom role for data
            self.history_list.addItem(item)

    def _on_history_item_double_clicked(self, item):
        entry = item.data(1000)
        # Attempt to connect to the selected device
        asyncio.create_task(self._connect_to_history_device(entry))

    async def _connect_to_history_device(self, entry):
        self.search_label.setText(f"Connecting to {entry['device_name']}...")
        try:
            await self.remote_control.pair(
                entry['ip'],
                lambda: QInputDialog.getText(self, 'TV Remote Control', 'Enter the code:'),
            )
            device_info = self.remote_control.device_info()
            if device_info:
                self.search_label.setText(f"{device_info['manufacturer']} {device_info['model']}")
                self.is_connected = True
                # Update history with latest connection
                history.update_history(entry['device_name'], entry['ip'], entry.get('favorite', False))
                self._refresh_history_list()
        except Exception as exc:
            self.search_label.setText('Not connected')
            _LOGGER.error('History Connect Error: %s', exc)

    def add_button(
        self,
        layout: QGridLayout,
        text: str,
        row: int,
        col: int,
        handler: Callable | None = None,
    ) -> None:
        button = QPushButton(text)
        button.setFixedSize(60, 60)

        layout.addWidget(button, row, col)

        if handler:
            button.clicked.connect(handler)

    def closeEvent(self, event):  # noqa: N802
        event.ignore()
        self.hide()

    def _main_window_configure(self) -> None:
        self.setWindowTitle('TV Remote Control')
        self.setFixedSize(300, 560)
        self.setStyleSheet("""
            QLabel { color: white; font-size: 16px; }
            QPushButton {
                background-color: #333;
                color: white;
                font-size: 14px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QPushButton:pressed {
                background-color: #555;
            }
            QInputDialog {
                background-color: #1E1E1E;
            }
            QDialog QPushButton {
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 10px;
                color: white;
            }
            QDialog QLineEdit {
                font-size: 18px;
                padding: 6px;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                color: white;
                background-color: #444;
            }
            MainWindow {
                background-color: #1E1E1E;
            }
        """)

    def _on_tray_icon_activated(self, reason: int) -> None:
        if reason == QSystemTrayIcon.Trigger:
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
        QApplication.instance().quit()

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
        self.search_label.setText('Search...')
        if self.is_connected:
            self.is_connected = False
            self.remote_control.disconnect()

        addrs: list = await self.remote_control.find_android_tv()
        if len(addrs) > 0:
            self.search_label.setText(f'Pair to {addrs[0]}')

            try:
                await self.remote_control.pair(
                    addrs[0],
                    lambda: QInputDialog.getText(self, 'TV Remote Control', 'Enter the code:'),
                )
                device_info = self.remote_control.device_info()
            except Exception as exc:
                self.search_label.setText('Not connected')
                _LOGGER.error('Pair Error: %s', exc)
                return

            if device_info:
                self.search_label.setText(f"{device_info['manufacturer']} {device_info['model']}")
                self.is_connected = True
        else:
            self.search_label.setText('Android TV not found')


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
