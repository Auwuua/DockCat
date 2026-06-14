from __future__ import annotations

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from dockcat.app import DockCatApplication


def main():
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("DockCat")
    app.setOrganizationName("DockCat")

    # 使窗口可以穿透鼠标事件（除猫区域外）
    app.setQuitOnLastWindowClosed(False)

    dockcat = DockCatApplication()
    dockcat.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
