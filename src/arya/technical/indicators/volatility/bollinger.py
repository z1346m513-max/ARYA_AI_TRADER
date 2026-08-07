"""اندیکاتور نوسان: باندهای بولینگر (Bollinger Bands)."""
from __future__ import annotations

import pandas as pd

from arya.models.analysis_result import IndicatorResult
from arya.technical.indicators.base import Indicator, IndicatorRegistry


@IndicatorRegistry.register("bollinger")
class BollingerBandsIndicator(Indicator):
    name = "bollinger"
    group = "volatility"

    def compute(self, df: pd.DataFrame) -> IndicatorResult:
        period = int(self.params.get("period", 20))
        std_dev = float(self.params.get("std_dev", 2))

        mid = df["close"].rolling(window=period).mean()
        std = df["close"].rolling(window=period).std()
        upper = mid + std_dev * std
        lower = mid - std_dev * std

        last_close = float(df["close"].iloc[-1])
        last_upper = float(upper.iloc[-1]) if pd.notna(upper.iloc[-1]) else last_close
        last_lower = float(lower.iloc[-1]) if pd.notna(lower.iloc[-1]) else last_close
        last_mid = float(mid.iloc[-1]) if pd.notna(mid.iloc[-1]) else last_close

        band_width = max(last_upper - last_lower, 1e-9)
        # موقعیت قیمت داخل باند: -1 (روی باند پایین) .. +1 (روی باند بالا)
        position = (2 * (last_close - last_lower) / band_width) - 1
        score = self._clamp(-position * 0.5)  # نزدیکی به باند بالا => احتمال اصلاح (امتیاز منفی ملایم)

        alerts: list[str] = []
        if last_close >= last_upper:
            alerts.append("upper_breakout")
        elif last_close <= last_lower:
            alerts.append("lower_breakout")

        return IndicatorResult(
            name=self.name,
            group=self.group,
            value={
                "upper": round(last_upper, 4),
                "mid": round(last_mid, 4),
                "lower": round(last_lower, 4),
            },
            score=score,
            weight=self.weight,
            triggered_alerts=alerts,
        )
