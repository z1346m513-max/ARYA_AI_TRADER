"""Smoke tests for the optional PySide6 dashboard shell."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from arya.ui.windows.main_window import MainWindow


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_dashboard_is_rtl_and_never_claims_live_prices_without_a_provider(qt_app):
    window = MainWindow()
    try:
        assert window.layoutDirection() == Qt.LayoutDirection.RightToLeft
        assert "Provider آنلاین پیکربندی نشده" in window.status_label.text()
        assert not window.symbol_search.isEnabled()
        assert not window.market_select.isEnabled()
        values = [label.text() for label in window.findChildren(QLabel)]
        assert values.count("—") == 4
    finally:
        window.close()
