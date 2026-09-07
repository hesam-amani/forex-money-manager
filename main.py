#!/usr/bin/env python3
"""Entry point for FMM — Forex Money Manager"""

from __future__ import annotations

import sys

from fmm.core.constants import APP_NAME
from fmm.ui.main_window import MainWindow
from fmm.ui.styles import STYLESHEET
from PySide6.QtWidgets import QApplication  # pyright: ignore[reportMissingImports]


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
