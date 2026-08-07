"""اندیکاتور مومنتوم: MACD (Moving Average Convergence Divergence)."""
from __future__ import annotations

import pandas as pd

from arya.models.analysis_result import IndicatorResult
from arya.technical.indicators.base import Indicator, IndicatorRegistry


@IndicatorRegistry.register("macd")
class MACDIndicator(Indicator):
    name = "macd"
    group = "momentum"

    def compute(self, df: pd.DataFrame) -> IndicatorResult:
        fast = int(self.params.get("fast", 12))
        slow = int(self.params.get("slow", 26))
        signal_period = int(self.params.get("signal", 9))

        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        last_macd = float(macd_line.iloc[-1])
        last_signal = float(signal_line.iloc[-1])
        last_hist = float(histogram.iloc[-1])
        last_price = float(df["close"].iloc[-1]) or 1.0

        # نرمال‌سازی بر اساس درصد قیمت تا مقیاس‌ناپذیر (scale-free) باشد
        score = self._clamp((last_hist / last_price) * 20)

        alerts: list[str] = []
        prev_hist = float(histogram.iloc[-2]) if len(histogram) > 1 else 0.0
        if prev_hist < 0 <= last_hist:
            alerts.append("bullish_cross")
        elif prev_hist > 0 >= last_hist:
            alerts.append("bearish_cross")

        return IndicatorResult(
            name=self.name,
            group=self.group,
            value={
                "macd": round(last_macd, 4),
                "signal": round(last_signal, 4),
                "histogram": round(last_hist, 4),
            },
            score=score,
            weight=self.weight,
            triggered_alerts=alerts,
        )
