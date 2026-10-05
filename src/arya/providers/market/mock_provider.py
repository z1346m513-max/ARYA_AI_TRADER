"""
Provider آزمایشی فقط برای بورس ایران.

داده‌ی OHLCV مصنوعی ولی Deterministic (بر اساس seed) تولید می‌کند تا
توسعه و تست پایپ‌لاین بدون وابستگی به TSETMC ممکن باشد.

نمادهای نمونه از صنایع رایج TSE انتخاب شده‌اند.
ارز دیجیتال، فارکس و سهام خارجی در این Provider وجود ندارند.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np

from arya.models.market_data import Candle, OHLCVSeries, Symbol
from arya.providers.base import MarketDataProvider, ProviderRegistry


_TSE_SAMPLE_SYMBOLS: list[tuple[str, str, str]] = [
    ("FOOLAD", "فولاد مبارکه اصفهان", "فلزات اساسی"),
    ("FARS", "فارس", "محصولات شیمیایی"),
    ("SHASTA", "سرمایه‌گذاری تأمین اجتماعی", "سرمایه‌گذاری‌ها"),
    ("KHODRO", "ایران خودرو", "خودرو و ساخت قطعات"),
    ("WEB", "بانک اقتصاد نوین", "بانک‌ها و مؤسسات اعتباری"),
    ("SHIRAZ", "پتروشیمی شیراز", "محصولات شیمیایی"),
    ("KHEGOM", "ایران‌خودرو دیزل", "خودرو و ساخت قطعات"),
    ("SEPAH", "بانک سپه", "بانک‌ها و مؤسسات اعتباری"),
    ("KARGAR", "سیمان کارون", "سیمان، آهک و گچ"),
    ("DAPCO", "داروسازی دانا", "مواد و محصولات دارویی"),
]


@ProviderRegistry.register("mock")
class MockMarketProvider(MarketDataProvider):
    name = "mock"

    def __init__(self, market: str = "stock", seed: int = 42):
        if market not in ("stock", "", None):
            raise ValueError(
                f"ARYA در نسخه TSE-only فقط بازار stock را پشتیبانی می‌کند؛ دریافت شد: {market!r}"
            )
        self.market = "stock"
        self._rng = np.random.default_rng(seed)

    def list_symbols(self) -> list[Symbol]:
        symbols = []
        for t, n, ind in _TSE_SAMPLE_SYMBOLS:
            try:
                symbols.append(
                    Symbol(
                        ticker=t,
                        market="stock",
                        name=n,
                        currency="IRR",
                        industry=ind,
                    )
                )
            except TypeError:
                symbols.append(Symbol(ticker=t, market="stock", name=n))
        return symbols

    def fetch_ohlcv(self, symbol: Symbol, timeframe: str, limit: int = 200) -> OHLCVSeries:
        candles = self._generate_candles(symbol.ticker, limit)
        return OHLCVSeries(symbol=symbol, timeframe=timeframe, candles=candles)

    def _generate_candles(self, ticker: str, limit: int) -> list[Candle]:
        local_rng = np.random.default_rng(abs(hash(ticker)) % (2**32))
        base_price = 1000 + (abs(hash(ticker)) % 9000)
        prices = [float(base_price)]
        for i in range(1, limit):
            drift = 0.15 * math.sin(i / 15)
            shock = local_rng.normal(loc=drift, scale=1.2)
            prices.append(max(10.0, prices[-1] + shock))

        now = datetime.now(timezone.utc)
        candles: list[Candle] = []
        for i, close in enumerate(prices):
            open_ = prices[i - 1] if i > 0 else close
            high = max(open_, close) + abs(local_rng.normal(0, 0.5))
            low = min(open_, close) - abs(local_rng.normal(0, 0.5))
            volume = float(local_rng.integers(50_000, 2_000_000))
            candles.append(
                Candle(
                    timestamp=now - timedelta(days=(limit - i)),
                    open=round(open_, 2),
                    high=round(high, 2),
                    low=round(max(low, 1.0), 2),
                    close=round(close, 2),
                    volume=volume,
                )
            )
        return candles
