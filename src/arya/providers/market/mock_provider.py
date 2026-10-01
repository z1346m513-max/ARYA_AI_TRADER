"""
Provider آزمایشی (Mock) که داده‌ی OHLCV مصنوعی ولی واقع‌گرایانه تولید می‌کند.
تا زمانی که اتصال واقعی به TSETMC / Binance / Oanda در فازهای بعدی اضافه شود،
تمام توسعه و تست پایپ‌لاین با همین Provider انجام می‌شود؛ به همین دلیل رفتار آن
Deterministic (بر اساس seed) است تا تست‌ها Reproducible بمانند.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np

from arya.models.market_data import Candle, OHLCVSeries, Symbol
from arya.providers.base import MarketDataProvider, ProviderRegistry


_SAMPLE_SYMBOLS = {
    "stock": [("FOOLAD", "فولاد مبارکه"), ("SHASTA", "پتروشیمی شازند")],
    "crypto": [("BTCUSDT", "Bitcoin"), ("ETHUSDT", "Ethereum")],
    "forex": [("EURUSD", "Euro/US Dollar"), ("GBPUSD", "Pound/US Dollar")],
}


@ProviderRegistry.register("mock")
class MockMarketProvider(MarketDataProvider):
    name = "mock"

    def __init__(self, market: str = "stock", seed: int = 42):
        self.market = market
        self._rng = np.random.default_rng(seed)

    def list_symbols(self) -> list[Symbol]:
        return [
            Symbol(ticker=t, market=self.market, name=n)
            for t, n in _SAMPLE_SYMBOLS.get(self.market, [])
        ]

    def fetch_ohlcv(self, symbol: Symbol, timeframe: str, limit: int = 200) -> OHLCVSeries:
        candles = self._generate_candles(symbol.ticker, limit)
        return OHLCVSeries(symbol=symbol, timeframe=timeframe, candles=candles)

    def _generate_candles(self, ticker: str, limit: int) -> list[Candle]:
        # seed اختصاصی برای هر نماد تا داده‌ها بین نمادها متفاوت باشند
        local_rng = np.random.default_rng(abs(hash(ticker)) % (2**32))
        base_price = 100 + (abs(hash(ticker)) % 500)
        prices = [base_price]
        # حرکت قیمت: random walk + یک روند ملایم سینوسی برای واقعی‌تر شدن
        for i in range(1, limit):
            drift = 0.15 * math.sin(i / 15)
            shock = local_rng.normal(loc=drift, scale=1.2)
            prices.append(max(1.0, prices[-1] + shock))

        now = datetime.now(timezone.utc)
        candles: list[Candle] = []
        for i, close in enumerate(prices):
            open_ = prices[i - 1] if i > 0 else close
            high = max(open_, close) + abs(local_rng.normal(0, 0.5))
            low = min(open_, close) - abs(local_rng.normal(0, 0.5))
            volume = float(local_rng.integers(1_000, 50_000))
            candles.append(
                Candle(
                    timestamp=now - timedelta(days=(limit - i)),
                    open=round(open_, 2),
                    high=round(high, 2),
                    low=round(max(low, 0.1), 2),
                    close=round(close, 2),
                    volume=volume,
                )
            )
        return candles
