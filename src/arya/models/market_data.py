"""مدل‌های داده‌ی بازار: کندل، سری زمانی و نماد (فقط بورس ایران)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd


@dataclass(frozen=True)
class Symbol:
    """نماد بازار سرمایه ایران."""

    ticker: str
    market: str = "stock"  # فقط stock
    name: str | None = None
    currency: str = "IRR"
    industry: str | None = None

    def __str__(self) -> str:
        return f"{self.ticker}@{self.market}"


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class OHLCVSeries:
    symbol: Symbol
    timeframe: str
    candles: list[Candle] = field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        if not self.candles:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        return pd.DataFrame(
            [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in self.candles
            ]
        ).set_index("timestamp")

    @property
    def last_close(self) -> float | None:
        return self.candles[-1].close if self.candles else None
