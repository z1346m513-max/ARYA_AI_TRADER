"""
استراتژی‌های خط پایه برای بک‌تست.

این استراتژی‌ها به‌عنوان معیار مقایسه (baseline) برای ارزیابی مدل‌های AI استفاده
می‌شوند. استراتژی پایه باید ساده، قابل فهم و تکرارپذیر باشد.

مهم: استراتژی‌ها فقط از داده‌های تا لحظهٔ تولید سیگنال استفاده می‌کنند و هرگز
به کندل‌های آینده دسترسی ندارند.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

import pandas as pd

from arya.backtest.models import Signal, Side


class Strategy(Protocol):
    """قرارداد استراتژی: یک سری کندل می‌گیرد و لیست سیگنال برمی‌گرداند."""

    name: str

    def generate_signals(self, df: pd.DataFrame) -> list[Signal]: ...


class BaseStrategy(ABC):
    """کلاس پایهٔ استراتژی با ابزارهای کمکی."""

    name: str = "base"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> list[Signal]:
        """سیگنال‌ها را بر اساس داده‌های *تا هر نقطه* تولید می‌کند.

        خروجی باید به‌گونه‌ای مرتب باشد که هر سیگنال فقط از داده‌های تا همان
        اندیس استفاده کرده باشد.
        """
        raise NotImplementedError

    @staticmethod
    def _safe_get(df: pd.DataFrame, col: str, idx: int) -> float:
        """دسترسی امن به مقدار یک ستون در اندیس مشخص."""
        if col not in df.columns or idx < 0 or idx >= len(df):
            return float("nan")
        return float(df[col].iloc[idx])


class MovingAverageCrossover(BaseStrategy):
    """استراتژی تقاطع میانگین متحرک ساده (SMA).

    سیگنال خرید وقتی SMA کوتاه‌مدت از بالای SMA بلندمدت عبور می‌کند (کراس صعودی)
    و سیگنال فروش وقتی برعکس (کراس نزولی).

    این استراتژی به‌عنوان baseline استفاده می‌شود تا عملکرد مدل‌های AI بتواند
    با یک معیار ساده و شفاف مقایسه شود.

    پارامترها:
        fast_period: دورهٔ SMA کوتاه‌مدت (پیش‌فرض: ۲۰)
        slow_period: دورهٔ SMA بلندمدت (پیش‌فرض: ۵۰)
    """

    name = "ma_crossover"

    def __init__(self, fast_period: int = 20, slow_period: int = 50):
        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) باید کوچکتر از slow_period ({slow_period}) باشد"
            )
        if fast_period < 1 or slow_period < 2:
            raise ValueError("دوره‌ها باید حداقل ۱ و ۲ باشند")
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, df: pd.DataFrame) -> list[Signal]:
        if "close" not in df.columns or len(df) < self.slow_period + 2:
            return []

        fast_sma = df["close"].rolling(window=self.fast_period).mean()
        slow_sma = df["close"].rolling(window=self.slow_period).mean()

        timestamps = df.index if not isinstance(df.index, pd.RangeIndex) else range(len(df))

        signals: list[Signal] = []
        prev_fast = prev_slow = None

        for i in range(len(df)):
            if pd.isna(fast_sma.iloc[i]) or pd.isna(slow_sma.iloc[i]):
                prev_fast = fast_sma.iloc[i]
                prev_slow = slow_sma.iloc[i]
                continue

            curr_fast = fast_sma.iloc[i]
            curr_slow = slow_sma.iloc[i]

            if prev_fast is not None and prev_slow is not None:
                if not pd.isna(prev_fast) and not pd.isna(prev_slow):
                    # کراس صعودی: SMA سریع از زیر به بالا عبور می‌کند
                    if prev_fast <= prev_slow and curr_fast > curr_slow:
                        ts = self._get_timestamp(df, i)
                        signals.append(Signal(
                            timestamp=ts,
                            side=Side.BUY,
                            bar_index=i,
                        ))
                    # کراس نزولی: SMA سریع از بالا به پایین عبور می‌کند
                    elif prev_fast >= prev_slow and curr_fast < curr_slow:
                        ts = self._get_timestamp(df, i)
                        signals.append(Signal(
                            timestamp=ts,
                            side=Side.SELL,
                            bar_index=i,
                        ))

            prev_fast = curr_fast
            prev_slow = curr_slow

        return signals

    @staticmethod
    def _get_timestamp(df: pd.DataFrame, idx: int) -> "datetime":
        """دریافت timestamp از اندیس دیتافریم."""
        from datetime import datetime
        ts = df.index[idx]
        if isinstance(ts, datetime):
            return ts
        try:
            return pd.Timestamp(ts).to_pydatetime()
        except Exception:
            return datetime.utcnow()


class MomentumStrategy(BaseStrategy):
    """استراتژی مومنتوم ساده: خرید وقتی بازده اخیر مثبت و قوی است.

    پارامترها:
        lookback: دورهٔ محاسبهٔ مومنتوم (پیش‌فرض: ۲۰)
        threshold: حداقل بازده برای تولید سیگنال خرید (پیش‌فرض: ۲٪)
    """

    name = "momentum"

    def __init__(self, lookback: int = 20, threshold: float = 0.02):
        if lookback < 2:
            raise ValueError("lookback باید حداقل ۲ باشد")
        self.lookback = lookback
        self.threshold = threshold

    def generate_signals(self, df: pd.DataFrame) -> list[Signal]:
        if "close" not in df.columns or len(df) < self.lookback + 1:
            return []

        close = df["close"]
        returns = close.pct_change(self.lookback)
        timestamps = df.index

        signals: list[Signal] = []
        for i in range(self.lookback, len(df)):
            if pd.isna(returns.iloc[i]):
                continue
            ret = float(returns.iloc[i])
            ts = self._get_timestamp(df, i)
            if ret > self.threshold:
                signals.append(Signal(timestamp=ts, side=Side.BUY, bar_index=i, strength=min(abs(ret) / self.threshold, 1.0)))
            elif ret < -self.threshold:
                signals.append(Signal(timestamp=ts, side=Side.SELL, bar_index=i, strength=min(abs(ret) / self.threshold, 1.0)))
        return signals

    @staticmethod
    def _get_timestamp(df: pd.DataFrame, idx: int) -> "datetime":
        from datetime import datetime
        ts = df.index[idx]
        if isinstance(ts, datetime):
            return ts
        try:
            return pd.Timestamp(ts).to_pydatetime()
        except Exception:
            return datetime.utcnow()
