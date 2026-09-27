import importlib.util

import pytest

from arya.config.settings import Settings


HAS_PYSIDE6 = importlib.util.find_spec("PySide6") is not None


@pytest.mark.skipif(not HAS_PYSIDE6, reason="PySide6 is an optional GUI dependency")
def test_persian_gui_boots_with_rtl(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import Qt

    from arya.ui.app import build_application

    settings = Settings.load()
    settings.app["app"]["language"] = "fa"
    settings.app["storage"]["path"] = str(tmp_path / "arya.db")
    settings.ui["theme"]["rtl"] = True

    app, window = build_application(settings)

    assert app.layoutDirection() == Qt.LayoutDirection.RightToLeft
    assert window.ticker_input.placeholderText() == "نماد را وارد کنید؛ مثال: فملی"
    assert window.ticker_input.layoutDirection() == Qt.LayoutDirection.RightToLeft

    window.close()
    app.quit()
