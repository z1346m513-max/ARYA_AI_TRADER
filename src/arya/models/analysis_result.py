"""مدل‌های خروجی موتور تحلیل، امتیازدهی و پیشنهاد نهایی."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Action(str, Enum):
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"


@dataclass
class IndicatorResult:
    """خروجی یک اندیکاتور برای یک نماد."""

    name: str
    group: str
    value: dict            # مقادیر خام محاسبه‌شده (مثلا rsi=65.2)
    score: float           # امتیاز نرمال‌شده [-1, 1]  (منفی=نزولی، مثبت=صعودی)
    weight: float
    triggered_alerts: list[str] = field(default_factory=list)


@dataclass
class SectionScore:
    """امتیاز یک بخش تحلیلی (تکنیکال، بنیادی، اخبار، ...)."""

    section: str
    score: float            # [-1, 1]
    confidence: float       # [0, 1]
    details: dict = field(default_factory=dict)


@dataclass
class RiskAssessment:
    risk_level: str          # low | medium | high
    risk_score: float        # [0, 1]
    max_position_size_pct: float
    stop_loss_pct: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class Recommendation:
    """خروجی نهایی موتور پیشنهاد - چیزی که به داشبورد نمایش داده می‌شود."""

    symbol: str
    overall_score: float        # [-1, 1]
    confidence: float           # [0, 1]
    trend_quality: float        # [0, 1]
    liquidity_strength: float   # [0, 1]
    action: Action
    reasons: list[str] = field(default_factory=list)
    risk: RiskAssessment | None = None
    section_scores: list[SectionScore] = field(default_factory=list)
    data_quality_run_id: str | None = None
