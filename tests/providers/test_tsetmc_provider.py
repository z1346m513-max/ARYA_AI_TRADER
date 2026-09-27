import pandas as pd
import pytest

from arya.models.market_data import Symbol
from arya.providers.base import ProviderRegistry
from arya.providers.market.tsetmc_provider import TsetmcMarketProvider


def test_tsetmc_provider_is_registered():
    provider = ProviderRegistry.create("tsetmc", market="stock")
    assert isinstance(provider, TsetmcMarketProvider)


def test_normalize_history_maps_expected_columns():
    raw = pd.DataFrame(
        {
            "date": ["2026-09-25", "2026-09-26"],
            "open": [100, 101],
            "high": [105, 106],
            "low": [99, 100],
            "close": [104, 105],
            "volume": [1000, 1200],
        }
    )

    normalized = TsetmcMarketProvider._normalize_history(raw)

    assert list(normalized.columns) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    assert len(normalized) == 2
    assert normalized.iloc[-1]["close"] == 105


def test_normalize_history_rejects_missing_required_column():
    raw = pd.DataFrame(
        {
            "date": ["2026-09-25"],
            "open": [100],
            "high": [105],
            "low": [99],
            "close": [104],
        }
    )

    with pytest.raises(ValueError, match="volume"):
        TsetmcMarketProvider._normalize_history(raw)


def test_fetch_ohlcv_with_fake_ticker(monkeypatch):
    class FakeTicker:
        title = "ملی صنایع مس ایران"

        def __init__(self, symbol, adjust=False):
            assert symbol == "فملی"
            assert adjust is False
            self.history = pd.DataFrame(
                {
                    "date": pd.to_datetime(
                        ["2026-09-25", "2026-09-26", "2026-09-27"]
                    ),
                    "open": [24000, 24500, 25000],
                    "high": [24600, 25100, 25500],
                    "low": [23800, 24300, 24900],
                    "close": [24500, 25000, 25290],
                    "volume": [100000000, 200000000, 300823812],
                }
            )

    monkeypatch.setattr(
        "arya.providers.market.tsetmc_provider.Ticker", FakeTicker
    )

    provider = TsetmcMarketProvider()
    series = provider.fetch_ohlcv(
        Symbol(ticker="فملی", market="stock"), timeframe="1d", limit=2
    )

    assert series.symbol.name == "ملی صنایع مس ایران"
    assert len(series.candles) == 2
    assert series.candles[-1].close == 25290
    assert series.candles[-1].volume == 300823812


def test_fetch_ohlcv_rejects_non_daily_timeframe():
    provider = TsetmcMarketProvider()
    with pytest.raises(ValueError, match="timeframe"):
        provider.fetch_ohlcv(
            Symbol(ticker="فملی", market="stock"), timeframe="1h", limit=10
        )
