from arya.models.market_data import Symbol
from arya.providers.market.mock_provider import MockMarketProvider


def test_list_symbols():
    provider = MockMarketProvider(market="stock")
    symbols = provider.list_symbols()
    assert len(symbols) > 0
    assert all(s.market == "stock" for s in symbols)


def test_fetch_ohlcv_returns_requested_length():
    provider = MockMarketProvider(market="crypto")
    symbol = Symbol(ticker="BTCUSDT", market="crypto")
    series = provider.fetch_ohlcv(symbol, timeframe="1d", limit=100)
    assert len(series.candles) == 100
    assert series.last_close is not None


def test_fetch_ohlcv_is_deterministic_per_ticker():
    provider = MockMarketProvider(market="stock")
    s1 = Symbol(ticker="FOOLAD", market="stock")
    series_a = provider.fetch_ohlcv(s1, timeframe="1d", limit=50)
    series_b = provider.fetch_ohlcv(s1, timeframe="1d", limit=50)
    assert [c.close for c in series_a.candles] == [c.close for c in series_b.candles]
