"""اندیکاتور مومنتوم: RSI (Relative Strength Index)."""
from __future__ import annotations

import pandas as pd

from arya.models.analysis_result import IndicatorResult
from arya.technical.indicators.base import Indicator, IndicatorRegistry


@IndicatorRegistry.register("rsi")
class RSIIndicator(Indicator):
    name = "rsi"
    group = "momentum"

    def compute(self, df: pd.DataFrame) -> IndicatorResult:
        period = int(self.params.get("period", 14))
        overbought = self.params.get("overbought", 70)
        oversold = self.params.get("oversold", 30)

        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(window=period).mean()
        loss = (-delta.clip(upper=0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, 1e-9)
        rsi = 100 - (100 / (1 + rs))
        last_rsi = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else 50.0

        # نرمال‌سازی RSI (0..100) به امتیاز [-1, 1] حول محور 50
        score = self._clamp((last_rsi - 50) / 50)

        alerts: list[str] = []
        if last_rsi >= overbought:
            alerts.append("overbought")
        elif last_rsi <= oversold:
            alerts.append("oversold")

        return IndicatorResult(
            name=self.name,
            group=self.group,
            value={"rsi": round(last_rsi, 2)},
            score=score,
            weight=self.weight,
            triggered_alerts=alerts,
        )
