import json
from datetime import datetime

import pytest

from arya.models.market_data import Symbol
from arya.providers.market.tsetmc_provider import TsetmcMarketProvider, TsetmcProviderError


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_tsetmc_provider_resolves_symbol_and_maps_daily_ohlcv(monkeypatch):
    responses = {
        "/api/Instrument/GetInstrumentSearch/%D9%81%D9%88%D9%84%D8%A7%D8%AF": {
            "instrumentSearch": [{"insCode": "123", "lVal18AFC": "فولاد", "lVal30": "فولاد مبارکه"}]
        },
        "/api/ClosingPrice/GetClosingPriceDailyList/123/2": {
            "closingPriceDaily": [
                {"dEven": 20240102, "pClosing": 110, "priceFirst": 100, "priceYesterday": 100, "priceMin": 95, "priceMax": 115, "qTotTran5J": 2000},
                {"dEven": 20240103, "pClosing": 120, "priceFirst": 110, "priceYesterday": 110, "priceMin": 105, "priceMax": 125, "qTotTran5J": 3000},
            ]
        },
    }

    def fake_urlopen(request, timeout):
        from urllib.parse import urlsplit
        path = urlsplit(request.full_url).path
        if "Instrument" in path:
            path = path.replace("/api/Instrument/GetInstrumentSearch/", "/api/Instrument/GetInstrumentSearch/")
        if path not in responses:
            raise AssertionError(path)
        return FakeResponse(responses[path])

    monkeypatch.setattr("arya.providers.market.tsetmc_provider.urlopen", fake_urlopen)
    provider = TsetmcMarketProvider(base_url="https://example.test", retries=1)
    series = provider.fetch_ohlcv(Symbol("فولاد", "stock"), "1d", limit=2)

    assert series.symbol.name == "فولاد مبارکه"
    assert len(series.candles) == 2
    assert series.candles[0].close == 110
    assert series.candles[0].volume == 2000
    assert series.candles[0].timestamp == datetime(2024, 1, 2).replace(tzinfo=series.candles[0].timestamp.tzinfo)


def test_tsetmc_rejects_non_daily_timeframe():
    provider = TsetmcMarketProvider(retries=1)
    with pytest.raises(ValueError, match="روزانه"):
        provider.fetch_ohlcv(Symbol("فولاد", "stock"), "5m")


def test_tsetmc_reports_empty_history(monkeypatch):
    monkeypatch.setattr(
        "arya.providers.market.tsetmc_provider.urlopen",
        lambda request, timeout: FakeResponse({"instrumentSearch": [{"insCode": "123", "lVal18AFC": "فولاد"}]}),
    )
    provider = TsetmcMarketProvider(base_url="https://example.test", retries=1)
    with pytest.raises(TsetmcProviderError):
        provider.fetch_ohlcv(Symbol("فولاد", "stock"), "1d", limit=2)


@pytest.mark.parametrize("rows", [
    [{"insCode": "123", "lVal18AFC": "نماددیگر"}],
    [{"lVal18AFC": "فولاد"}],
    [{"insCode": "123", "lVal18AFC": "فولاد"}, {"insCode": "456", "lVal18AFC": "فولاد"}],
])
def test_instrument_requires_unique_exact_match(monkeypatch, rows):
    provider = TsetmcMarketProvider(retries=1)
    monkeypatch.setattr(provider, "_get_json", lambda path: {"instrumentSearch": rows})
    with pytest.raises(TsetmcProviderError, match="دقیق"):
        provider._resolve_instrument("فولاد")


@pytest.mark.parametrize("row", [{}, {"dEven": "20260230"}, {"dEven": "not-a-date"}])
def test_missing_or_invalid_source_date_never_becomes_now(row):
    with pytest.raises(TsetmcProviderError, match="تاریخ"):
        TsetmcMarketProvider._timestamp(row)


@pytest.mark.parametrize("field,value", [
    ("priceFirst", None), ("priceMax", None), ("priceMin", None),
    ("qTotTran5J", None), ("pClosing", "NaN"), ("priceMax", 80), ("qTotTran5J", -1),
])
def test_incomplete_or_inconsistent_candle_fails_closed(monkeypatch, field, value):
    row = {
        "dEven": 20240102, "pClosing": 110, "priceFirst": 100,
        "priceMin": 95, "priceMax": 115, "qTotTran5J": 2000,
    }
    row[field] = value
    provider = TsetmcMarketProvider(retries=1)
    monkeypatch.setattr(provider, "_resolve_instrument", lambda ticker: ("123", None))
    monkeypatch.setattr(provider, "_get_json", lambda path: {"closingPriceDaily": [row]})
    with pytest.raises(TsetmcProviderError):
        provider.fetch_ohlcv(Symbol("فولاد", "stock"), "1d")


def test_market_watch_does_not_mislabel_retrieval_time(monkeypatch):
    provider = TsetmcMarketProvider(retries=1)
    monkeypatch.setattr(provider, "_get_json", lambda path: {"marketwatch": [{"lVal18AFC": "فولاد"}]})
    quote = provider.fetch_market_watch()[0]
    assert "timestamp" not in quote
    assert quote["source_timestamp"] is None
    assert datetime.fromisoformat(quote["retrieved_at_utc"]).utcoffset() is not None
