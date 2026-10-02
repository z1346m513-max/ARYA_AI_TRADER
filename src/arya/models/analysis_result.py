"""مدل‌های خروجی موتور تحلیل، امتیازدهی و پیشنهاد نهایی."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from arya.models.data_quality import DataCoverage, DataProvenance


class Action(str, Enum):
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"


@dataclass
class IndicatorResult:
    """خروجی یک اندیکاتور؛ مقدار خام و سیگنال نرمال‌شده جدا نگه داشته می‌شوند."""

    name: str
    group: str
    value: dict
    score: float
    weight: float
    triggered_alerts: list[str] = field(default_factory=list)
    confidence: float = 1.0
    provenance: DataProvenance | None = None


@dataclass
class SectionScore:
    """امتیاز یک بخش تحلیلی (تکنیکال، بنیادی، اخبار، ...)."""

    section: str
    score: float
    confidence: float
    details: dict = field(default_factory=dict)
    provenance: DataProvenance | None = None


@dataclass
class RiskAssessment:
    risk_level: str
    risk_score: float
    max_position_size_pct: float
    stop_loss_pct: float | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class Recommendation:
    """خروجی نهایی موتور پیشنهاد برای نمایش در داشبورد."""

    symbol: str
    overall_score: float
    confidence: float
    trend_quality: float
    liquidity_strength: float
    action: Action
    reasons: list[str] = field(default_factory=list)
    risk: RiskAssessment | None = None
    section_scores: list[SectionScore] = field(default_factory=list)
    coverage: DataCoverage = field(default_factory=DataCoverage)

    @property
    def confidence_is_data_limited(self) -> bool:
        """True وقتی confidence باید همراه با هشدار کمبود داده نمایش داده شود."""
        return self.coverage.ratio < 1.0
