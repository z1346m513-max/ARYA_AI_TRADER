import tempfile
from pathlib import Path

import pytest

from arya.app.bootstrap import AryaApp
from arya.config.settings import Settings
from arya.models.analysis_result import Action


@pytest.fixture
def app(tmp_path, monkeypatch):
    settings = Settings.load()
    # اجرای تست‌ها روی یک دیتابیس موقت تا فایل واقعی پروژه دست‌نخورده بماند
    settings.app["storage"]["path"] = str(tmp_path / "test_arya.db")
    return AryaApp(settings=settings)


def test_analyze_symbol_returns_valid_recommendation(app):
    rec = app.analyze_symbol("FOOLAD", market="stock")
    assert rec.symbol
    assert -1.0 <= rec.overall_score <= 1.0
    assert 0.0 <= rec.confidence <= 1.0
    assert rec.action in (Action.BUY, Action.HOLD, Action.SELL)
    assert rec.risk is not None
    assert rec.risk.risk_level in ("low", "medium", "high")
    assert len(rec.reasons) > 0


def test_list_symbols(app):
    symbols = app.list_symbols(market="crypto")
    assert len(symbols) > 0
