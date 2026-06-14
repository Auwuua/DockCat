from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent, QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QApplication

from ..core.state import CatState, AppLanguage


class CatInteraction:
    """Handles mouse interaction with the cat window."""

    def __init__(self, cat_window):
        self._cat_window = cat_window
        self._threshold = 20
        self._mouse_down_pos = None
        self._dragging = False

        self.on_click = None
        self.on_context_menu = None
        self.on_begin_drag = None
        self.on_drag = None
        self.on_end_drag = None

        cat_view = cat_window.cat_view
        cat_view.mousePressEvent = self._mouse_press
        cat_view.mouseMoveEvent = self._mouse_move
        cat_view.mouseReleaseEvent = self._mouse_release
        cat_view.setMouseTracking(True)

    def _mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            if self.on_context_menu:
                self.on_context_menu(event)
            return
        self._mouse_down_pos = event.globalPosition().toPoint()
        self._dragging = False

    def _mouse_move(self, event: QMouseEvent):
        if self._mouse_down_pos is None:
            return
        current = event.globalPosition().toPoint()
        dist = (current - self._mouse_down_pos).manhattanLength()
        if not self._dragging and dist >= self._threshold:
            self._dragging = True
            if self.on_begin_drag:
                self.on_begin_drag()
        if self._dragging and self.on_drag:
            self.on_drag((current.x(), current.y()))

    def _mouse_release(self, event: QMouseEvent):
        current = event.globalPosition().toPoint()
        if self._dragging:
            if self.on_end_drag:
                self.on_end_drag((current.x(), current.y()))
        elif self.on_click:
            self.on_click(event)
        self._mouse_down_pos = None
        self._dragging = False
