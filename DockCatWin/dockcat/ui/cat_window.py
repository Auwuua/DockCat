from __future__ import annotations

import math
from typing import Optional, Callable

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QMouseEvent, QAction, QIcon, QFontMetrics, \
    QFont, QColor, QPalette, QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QApplication, QMenu, QSystemTrayIcon, QMainWindow,
    QDialog, QFormLayout, QCheckBox, QSpinBox, QDoubleSpinBox,
    QComboBox, QSlider, QDialogButtonBox, QTabWidget, QTextEdit,
    QScrollArea, QGridLayout, QGroupBox
)

from ..core.state import (
    CatState, ReminderType, OutingPhase, AppLanguage, CatActivityScope
)
from ..core.state_machine import CatStateMachine
from ..core.settings import AppSettings, SettingsStore
from ..core.strings import AppStrings
from ..core.outing import OutingCollectable
from ..core.activity_space import ActivitySpace, get_current_activity_space


class CatView(QWidget):
    """Widget that renders the cat image."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._mirrored = False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

    def set_image(self, pixmap: Optional[QPixmap], mirrored: bool = False):
        self._pixmap = pixmap
        self._mirrored = mirrored
        if pixmap and not pixmap.isNull():
            self.setFixedSize(pixmap.size())
        self.update()

    def set_mirrored(self, mirrored: bool):
        if self._mirrored != mirrored:
            self._mirrored = mirrored
            self.update()

    def paintEvent(self, event):
        if self._pixmap and not self._pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            if self._mirrored:
                painter.scale(-1, 1)
                painter.drawPixmap(-self.width(), 0, self._pixmap)
            else:
                painter.drawPixmap(0, 0, self._pixmap)
            painter.end()


class SpeechBubble(QWidget):
    """Speech bubble widget with optional buttons and input."""

    primary_clicked = pyqtSignal()
    secondary_clicked = pyqtSignal()
    value_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value_input: Optional[QLineEdit] = None
        self._image_label: Optional[QLabel] = None
        self._image_title: Optional[QLabel] = None
        self._message_label: Optional[QLabel] = None
        self._primary_btn: Optional[QPushButton] = None
        self._secondary_btn: Optional[QPushButton] = None
        self._on_primary_cb = None
        self._on_secondary_cb = None
        self._on_value_cb = None
        self._setup_ui()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_callbacks(self, on_primary=None, on_secondary=None, on_value=None):
        self._on_primary_cb = on_primary
        self._on_secondary_cb = on_secondary
        self._on_value_cb = on_value

    def clear_callbacks(self):
        self._on_primary_cb = None
        self._on_secondary_cb = None
        self._on_value_cb = None

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._message_label = QLabel()
        self._message_label.setWordWrap(True)
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self._message_label.setFont(font)
        layout.addWidget(self._message_label)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setFixedSize(80, 80)
        self._image_label.hide()
        layout.addWidget(self._image_label)

        self._image_title = QLabel()
        self._image_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_title.setStyleSheet("font-weight: bold;")
        self._image_title.hide()
        layout.addWidget(self._image_title)

        self._value_input = QLineEdit()
        self._value_input.hide()
        layout.addWidget(self._value_input)

        btn_layout = QHBoxLayout()
        self._secondary_btn = QPushButton()
        self._secondary_btn.clicked.connect(self._on_secondary_clicked)
        self._secondary_btn.hide()
        btn_layout.addWidget(self._secondary_btn)

        self._primary_btn = QPushButton()
        self._primary_btn.clicked.connect(self._on_primary_clicked)
        btn_layout.addWidget(self._primary_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.setStyleSheet("""
            SpeechBubble {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
        """)

    def _on_primary_clicked(self):
        if self._value_input and self._value_input.isVisible():
            if self._on_value_cb:
                self._on_value_cb(self._value_input.text())
        else:
            if self._on_primary_cb:
                self._on_primary_cb()

    def _on_secondary_clicked(self):
        if self._on_secondary_cb:
            self._on_secondary_cb()

    def configure(self, message: str, primary_title: str,
                  secondary_title: Optional[str] = None):
        self._message_label.setText(message)
        self._primary_btn.setText(primary_title)
        self._image_label.hide()
        self._image_title.hide()
        self._value_input.hide()
        self._secondary_btn.setText(secondary_title or "")
        self._secondary_btn.setVisible(secondary_title is not None)
        self.adjustSize()

    def configure_image(self, message: str, image: Optional[QPixmap],
                        image_title: Optional[str], primary_title: str):
        self._message_label.setText(message)
        self._primary_btn.setText(primary_title)
        self._secondary_btn.hide()
        self._value_input.hide()
        if image and not image.isNull():
            self._image_label.setPixmap(image.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                                     Qt.TransformationMode.SmoothTransformation))
            self._image_label.show()
        else:
            self._image_label.hide()
        if image_title:
            self._image_title.setText(image_title)
            self._image_title.show()
        else:
            self._image_title.hide()
        self.adjustSize()

    def configure_input(self, message: str, value: str,
                        primary_title: str, secondary_title: str,
                        minute_unit: str = "分钟"):
        self._message_label.setText(message)
        self._primary_btn.setText(primary_title)
        self._secondary_btn.setText(secondary_title)
        self._secondary_btn.show()
        self._value_input.setText(value)
        self._value_input.show()
        self._image_label.hide()
        self._image_title.hide()
        self.adjustSize()


class CatWindow(QWidget):
    """Frameless, transparent window showing the cat."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._bubble = SpeechBubble(self)
        self._bubble.hide()
        self._layout.addWidget(self._bubble, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._cat_view = CatView(self)
        self._layout.addWidget(self._cat_view, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(self._layout)

    @property
    def cat_view(self) -> CatView:
        return self._cat_view

    @property
    def bubble(self) -> SpeechBubble:
        return self._bubble

    def show_at(self, anchor: tuple[float, float]):
        x, y = anchor
        self.move(int(x), int(y))
        self.show()

    def set_anchor(self, anchor: tuple[float, float]):
        x, y = anchor
        self.move(int(x), int(y))

    def set_image(self, pixmap: Optional[QPixmap], mirrored: bool = False,
                  source_size: Optional[tuple[int, int]] = None):
        self._cat_view.set_image(pixmap, mirrored)

    def set_mirrored(self, mirrored: bool):
        self._cat_view.set_mirrored(mirrored)

    def show_bubble(self, message: str, primary_title: str,
                    secondary_title: Optional[str] = None):
        self._bubble.configure(message, primary_title, secondary_title)
        self._bubble.show()
        self._adjust_for_bubble()

    def show_image_bubble(self, message: str, image: Optional[QPixmap],
                          image_title: Optional[str], primary_title: str):
        self._bubble.configure_image(message, image, image_title, primary_title)
        self._bubble.show()
        self._adjust_for_bubble()

    def show_input_bubble(self, message: str, value: str,
                          primary_title: str, secondary_title: str,
                          minute_unit: str = "分钟"):
        self._bubble.configure_input(message, value, primary_title, secondary_title, minute_unit)
        self._bubble.show()
        self._adjust_for_bubble()

    def hide_bubble(self):
        self._bubble.hide()
        self._adjust_for_bubble()

    def _adjust_for_bubble(self):
        self.adjustSize()
