from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QApplication

from ..core.state import CatState, AppLanguage


class TrayManager:
    """Manage system tray icon and context menus."""

    def __init__(self, window, icon_path: Optional[str] = None):
        self._window = window
        self._tray = QSystemTrayIcon()
        if icon_path:
            self._tray.setIcon(QIcon(icon_path))
        else:
            # Create a simple default icon
            pix = QPixmap(32, 32)
            pix.fill(Qt.GlobalColor.transparent)
            self._tray.setIcon(QIcon(pix))
        self._tray.show()

        self.on_pet = None
        self.on_outing = None
        self.on_settings = None
        self.on_quit = None
        self.on_recall = None

        self._language = AppLanguage.CHINESE

    def set_language(self, language: AppLanguage):
        self._language = language

    def build_menu(self, state: Optional[CatState] = None):
        menu = QMenu()

        pet_action = menu.addAction("摸摸猫" if self._language == AppLanguage.CHINESE else "Pet cat")
        pet_action.triggered.connect(lambda: self._call(self.on_pet))

        outing_action = menu.addAction("出门" if self._language == AppLanguage.CHINESE else "Go out")
        outing_action.triggered.connect(lambda: self._call(self.on_outing))

        if state and state.name == "outing":
            recall_action = menu.addAction("召回" if self._language == AppLanguage.CHINESE else "Recall")
            recall_action.triggered.connect(lambda: self._call(self.on_recall))

        menu.addSeparator()

        settings_action = menu.addAction(
            "设置" if self._language == AppLanguage.CHINESE else "Settings"
        )
        settings_action.triggered.connect(lambda: self._call(self.on_settings))

        quit_action = menu.addAction(
            "退出" if self._language == AppLanguage.CHINESE else "Quit"
        )
        quit_action.triggered.connect(lambda: self._call(self.on_quit))

        self._tray.setContextMenu(menu)

    def show_context_menu(self, pos):
        # This is handled through the tray icon
        pass

    @staticmethod
    def _call(callback):
        if callback:
            callback()
