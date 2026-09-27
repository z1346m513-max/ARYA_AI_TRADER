"""
Risk Manager: ریسک قابل تنظیم از طریق Analysis Profile.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from arya.ai.reasoning.decision_engine import Decision
from arya.models.analysis_result import RiskAssessment


class RiskManager:
    def assess(
        self,
        df: pd.DataFrame,
        decision: Decision,
        config: dict[str, Any] | None = None,
    ) -> RiskAssessment:
        cfg = config or {}

        volatility_window = max(2, int(cfg.get("volatility_window", 14)))
        high_volatility = float(cfg.get("high_volatility_pct", 5.0))
        medium_volatility = float(cfg.get("medium_volatility_pct", 2.5))
        high_trend = float(cfg.get("high_trend_threshold", 0.30))
        medium_trend = float(cfg.get("medium_trend_threshold", 0.60))

        high_position = float(cfg.get("high_max_position_pct", 5.0))
        medium_position = float(cfg.get("medium_max_position_pct", 10.0))
        low_position = float(cfg.get("low_max_position_pct", 20.0))

        high_mult = float(cfg.get("high_stop_loss_multiplier", 1.5))
        medium_mult = float(cfg.get("medium_stop_loss_multiplier", 1.2))
        low_mult = float(cfg.get("low_stop_loss_multiplier", 1.0))

        volatility_pct = self._recent_volatility_pct(df, window=volatility_window)

        if volatility_pct > high_volatility or decision.trend_quality < high_trend:
            level = "high"
            risk_score = 0.75
            max_position = high_position
            stop_loss = max(volatility_pct * high_mult, 4.0)
        elif volatility_pct > medium_volatility or decision.trend_quality < medium_trend:
            level = "medium"
            risk_score = 0.45
            max_position = medium_position
            stop_loss = max(volatility_pct * medium_mult, 3.0)
        else:
            level = "low"
            risk_score = 0.2
            max_position = low_position
            stop_loss = max(volatility_pct * low_mult, 2.0)

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
