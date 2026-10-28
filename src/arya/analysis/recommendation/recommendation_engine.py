"""
Recommendation Engine: لایه‌ی هفتم پایپ‌لاین (Risk Manager -> Recommendation Engine -> Dashboard).

خروجی نهایی و انسانی‌خوان (Recommendation) را می‌سازد: امتیاز کلی، اطمینان،
کیفیت روند، قدرت نقدشوندگی (بر پایه‌ی حجم)، پیشنهاد خرید/نگهداری/فروش، دلایل و
ارزیابی ریسک. این همان چیزی است که به Dashboard نمایش داده می‌شود.
"""
from __future__ import annotations

import pandas as pd

from arya.ai.reasoning.decision_engine import Decision
from arya.models.analysis_result import Action, Recommendation, RiskAssessment, SectionScore


class RecommendationEngine:
    BUY_THRESHOLD = 0.25
    SELL_THRESHOLD = -0.25

    def build(
        self,
        symbol: str,
        df: pd.DataFrame,
        decision: Decision,
        risk: RiskAssessment,
        section_scores: list[SectionScore],
        data_quality_run_id: str | None = None,
    ) -> Recommendation:
        if decision.action_score >= self.BUY_THRESHOLD:
            action = Action.BUY
        elif decision.action_score <= self.SELL_THRESHOLD:
            action = Action.SELL
        else:
            action = Action.HOLD

        liquidity_strength = self._liquidity_strength(df)

        return Recommendation(
            symbol=symbol,
            overall_score=decision.action_score,
            confidence=decision.confidence,
            trend_quality=decision.trend_quality,
            liquidity_strength=liquidity_strength,
            action=action,
            reasons=decision.reasons,
            risk=risk,
            section_scores=section_scores,
            data_quality_run_id=data_quality_run_id,
        )

    @staticmethod
    def _liquidity_strength(df: pd.DataFrame, window: int = 20) -> float:
        """تقریب ساده از قدرت نقدشوندگی بر اساس حجم اخیر نسبت به میانگین بلندمدت."""
        if len(df) < 2 or "volume" not in df:
            return 0.0
        recent_avg = df["volume"].iloc[-min(window, len(df)):].mean()
        overall_avg = df["volume"].mean() or 1.0
        ratio = recent_avg / overall_avg
        return round(max(0.0, min(1.0, ratio / 2)), 4)
