"""Provider آزمایشی — فقط نمادهای فارسی بورس ایران."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np

from arya.models.market_data import Candle, OHLCVSeries, Symbol
from arya.providers.base import MarketDataProvider, ProviderRegistry
from arya.providers.market.ticker_map import to_tse_symbol

# فقط بورس ایران — نماد فارسی
_SAMPLE_STOCK: list[tuple[str, str]] = [
    ("فولاد", "فولاد مبارکه اصفهان"),
    ("فملی", "ملی صنایع مس ایران"),
    ("شپنا", "پالایش نفت اصفهان"),
    ("خودرو", "ایران خودرو"),
    ("خساپا", "سایپا"),
    ("شستا", "سرمایه‌گذاری تامین اجتماعی"),
    ("وبملت", "بانک ملت"),
    ("کگل", "گل‌گهر"),
]


@ProviderRegistry.register("mock")
class MockMarketProvider(MarketDataProvider):
    name = "mock"

    def __init__(self, market: str = "stock", seed: int = 42):
        if market != "stock":
            raise ValueError("Mock فقط market='stock' (بورس ایران) را پشتیبانی می‌کند")
        self.market = market
        self._rng = np.random.default_rng(seed)

    def list_symbols(self) -> list[Symbol]:
        return [
            Symbol(ticker=t, market="stock", name=n, currency="IRR")
            for t, n in _SAMPLE_STOCK
        ]

    def fetch_ohlcv(self, symbol: Symbol, timeframe: str, limit: int = 200) -> OHLCVSeries:
        ticker = to_tse_symbol(symbol.ticker)
        candles = self._generate_candles(ticker, limit)
        return OHLCVSeries(
            symbol=Symbol(
                ticker=ticker,
                market="stock",
                name=symbol.name,
                currency="IRR",
                industry=symbol.industry,
            ),
            timeframe=timeframe,
            candles=candles,
        )

    def _generate_candles(self, ticker: str, limit: int) -> list[Candle]:
        local_rng = np.random.default_rng(abs(hash(ticker)) % (2**32))
        base_price = 100 + (abs(hash(ticker)) % 500)
        prices = [float(base_price)]
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
