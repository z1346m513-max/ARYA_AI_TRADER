"""Entry point for the optional PySide6 dashboard."""

from __future__ import annotations

import sys


def run_dashboard(argv: list[str] | None = None) -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError(
            "رابط گرافیکی به وابستگی اختیاری PySide6 نیاز دارد؛ "
            "نصب کنید: pip install -e '.[gui]'"
        ) from exc

    from arya.ui.themes.palette import apply_theme
    from arya.ui.windows.main_window import MainWindow

    app = QApplication.instance() or QApplication(argv or sys.argv)
    app.setApplicationName("ARYA AI Trader")
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()
