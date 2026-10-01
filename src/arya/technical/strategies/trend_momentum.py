"""استراتژی روند-مومنتوم قابل توضیح و مناسب بک‌تست اولیه."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class StrategySignal:
    action: str
    score: float
    reasons: tuple[str, ...]


def trend_momentum_signal(
    df: pd.DataFrame,
    fast_period: int = 20,
    slow_period: int = 50,
    rsi_period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
) -> StrategySignal:
    """سیگنال فقط با اطلاعات تا آخرین کندل؛ برای توصیهٔ اجرایی نیست."""
    minimum = max(slow_period, rsi_period) + 2
    if len(df) < minimum:
        return StrategySignal("hold", 0.0, ("insufficient_history",))

    close = df["close"].astype(float)
    fast = close.ewm(span=fast_period, adjust=False).mean()
    slow = close.ewm(span=slow_period, adjust=False).mean()
    delta = close.diff()
    gains = delta.clip(lower=0).rolling(rsi_period).mean()
    losses = -delta.clip(upper=0).rolling(rsi_period).mean()
    rs = gains / losses.replace(0, pd.NA)
    rsi = (100 - (100 / (1 + rs))).fillna(50.0)

    reasons: list[str] = []
    score = 0.0
    if fast.iloc[-1] > slow.iloc[-1]:
        score += 0.5
        reasons.append("fast_ema_above_slow_ema")
    else:
        score -= 0.5
        reasons.append("fast_ema_below_slow_ema")
    if rsi.iloc[-1] < oversold:
        score += 0.25
        reasons.append("rsi_oversold")
    elif rsi.iloc[-1] > overbought:
        score -= 0.25
        reasons.append("rsi_overbought")
    else:
        reasons.append("rsi_neutral")

    action = "buy" if score >= 0.5 else ("sell" if score <= -0.5 else "hold")
    return StrategySignal(action, round(score, 4), tuple(reasons))
