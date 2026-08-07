"""
Risk Manager: لایه‌ی ششم پایپ‌لاین (AI Decision Engine -> Risk Manager -> Recommendation Engine).

بر اساس نوسان اخیر قیمت (تقریب ATR ساده) و کیفیت روند، سطح ریسک، حداکثر اندازه‌ی
پوزیشن پیشنهادی، و درصد حد ضرر را محاسبه می‌کند. این خروجی مستقل از AI Decision
Engine است تا بتوان بعداً منطق ریسک را (مثلا بر اساس نوسان بازار، همبستگی پرتفوی و...)
ارتقا داد بدون دست‌زدن به موتور تصمیم.
"""
from __future__ import annotations

import pandas as pd

from arya.ai.reasoning.decision_engine import Decision
from arya.models.analysis_result import RiskAssessment


class RiskManager:
    def assess(self, df: pd.DataFrame, decision: Decision) -> RiskAssessment:
        volatility_pct = self._recent_volatility_pct(df)

        if volatility_pct > 5 or decision.trend_quality < 0.3:
            level = "high"
            risk_score = 0.75
            max_position = 5.0
            stop_loss = max(volatility_pct * 1.5, 4.0)
        elif volatility_pct > 2.5 or decision.trend_quality < 0.6:
            level = "medium"
            risk_score = 0.45
            max_position = 10.0
            stop_loss = max(volatility_pct * 1.2, 3.0)
        else:
            level = "low"
            risk_score = 0.2
            max_position = 20.0
            stop_loss = max(volatility_pct, 2.0)

        notes = [
            f"نوسان اخیر قیمت حدود {volatility_pct:.2f}% است.",
            f"کیفیت روند تشخیص‌داده‌شده: {decision.trend_quality:.2f}.",
        ]

        return RiskAssessment(
            risk_level=level,
            risk_score=risk_score,
            max_position_size_pct=max_position,
            stop_loss_pct=round(stop_loss, 2),
            notes=notes,
        )

    @staticmethod
    def _recent_volatility_pct(df: pd.DataFrame, window: int = 14) -> float:
        if len(df) < 2:
            return 0.0
        returns = df["close"].pct_change().dropna()
        recent = returns.iloc[-window:] if len(returns) >= window else returns
        return float(recent.std() * 100) if not recent.empty else 0.0
