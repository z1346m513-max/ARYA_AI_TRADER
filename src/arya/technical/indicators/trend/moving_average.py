"""اندیکاتورهای روند: میانگین متحرک ساده (SMA) و نمایی (EMA)."""
from __future__ import annotations

import pandas as pd

from arya.models.analysis_result import IndicatorResult
from arya.technical.indicators.base import Indicator, IndicatorRegistry


@IndicatorRegistry.register("sma")
class SMAIndicator(Indicator):
    name = "sma"
    group = "trend"

    def compute(self, df: pd.DataFrame) -> IndicatorResult:
        period = int(self.params.get("period", 20))
        sma = df["close"].rolling(window=period).mean()
        last_close = df["close"].iloc[-1]
        last_sma = sma.iloc[-1]

        alerts: list[str] = []
        if pd.notna(last_sma):
            pct_diff = (last_close - last_sma) / last_sma
            score = self._clamp(pct_diff * 5)  # نرمال‌سازی به بازه [-1,1]
            if self.params.get("cross_above") is None and last_close > last_sma:
                alerts.append("price_above_sma")
        else:
            score = 0.0

        return IndicatorResult(
            name=self.name,
            group=self.group,
            value={"sma": None if pd.isna(last_sma) else round(float(last_sma), 4)},
            score=score,
            weight=self.weight,
            triggered_alerts=alerts,
        )


@IndicatorRegistry.register("ema")
class EMAIndicator(Indicator):
    name = "ema"
    group = "trend"

    def compute(self, df: pd.DataFrame) -> IndicatorResult:
        period = int(self.params.get("period", 50))
        ema = df["close"].ewm(span=period, adjust=False).mean()
        last_close = df["close"].iloc[-1]
        last_ema = ema.iloc[-1]

        pct_diff = (last_close - last_ema) / last_ema if last_ema else 0.0
        score = self._clamp(pct_diff * 5)

        alerts = ["price_above_ema"] if last_close > last_ema else []

        return IndicatorResult(
            name=self.name,
            group=self.group,
            value={"ema": round(float(last_ema), 4)},
            score=score,
            weight=self.weight,
            triggered_alerts=alerts,
        )
