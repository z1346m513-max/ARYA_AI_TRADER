"""اندیکاتور حجم: OBV (On-Balance Volume)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from arya.models.analysis_result import IndicatorResult
from arya.technical.indicators.base import Indicator, IndicatorRegistry


@IndicatorRegistry.register("obv")
class OBVIndicator(Indicator):
    name = "obv"
    group = "volume"

    def compute(self, df: pd.DataFrame) -> IndicatorResult:
        direction = np.sign(df["close"].diff().fillna(0))
        obv = (direction * df["volume"]).cumsum()

        window = min(20, len(obv))
        recent_slope = 0.0
        if window > 1:
            recent = obv.iloc[-window:]
            recent_slope = (recent.iloc[-1] - recent.iloc[0]) / (abs(recent.iloc[0]) + 1e-9)

        score = self._clamp(recent_slope)

        alerts: list[str] = []
        if score > 0.3:
            alerts.append("volume_confirms_uptrend")
        elif score < -0.3:
            alerts.append("volume_confirms_downtrend")

        return IndicatorResult(
            name=self.name,
            group=self.group,
            value={"obv": round(float(obv.iloc[-1]), 2)},
            score=score,
            weight=self.weight,
            triggered_alerts=alerts,
        )
