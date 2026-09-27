"""PySide6 application entry point for ARYA's Persian RTL desktop UI."""

from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication, QLocale, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from arya.config.settings import Settings
from arya.ui.main_window import MainWindow


def build_application(settings: Settings | None = None) -> tuple[QApplication, MainWindow]:
    settings = settings or Settings.load()
    app = QApplication.instance() or QApplication(sys.argv)

    language = settings.app.get("app", {}).get("language", "fa")
    rtl = settings.ui.get("theme", {}).get("rtl", True) and language == "fa"

    if rtl:
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        QCoreApplication.setApplicationName("ARYA AI Trader")
        QLocale.setDefault(QLocale(QLocale.Language.Persian, QLocale.Country.Iran))
    else:
        app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    font_cfg = settings.ui.get("theme", {})
    family = font_cfg.get("font_family", "")
    size = int(font_cfg.get("font_size", 11))
    if family:
        app.setFont(QFont(family, size))
    else:
        app.setFont(QFont("", size))

    window = MainWindow(settings)
    return app, window


def main() -> int:
    settings = Settings.load()
    app, window = build_application(settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
