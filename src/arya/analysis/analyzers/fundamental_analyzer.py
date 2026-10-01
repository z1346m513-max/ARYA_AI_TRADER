"""تحلیل بنیادی محافظه‌کارانه؛ دادهٔ ناقص امتیاز مثبت جعلی تولید نمی‌کند."""
from __future__ import annotations

from arya.models.analysis_result import SectionScore
from arya.models.fundamentals import FundamentalMetrics


class FundamentalAnalyzer:
    section_name = "fundamental"

    def __init__(self, max_pe: float = 15.0, min_margin: float = 0.0, max_debt_to_equity: float = 2.0):
        self.max_pe = max_pe
        self.min_margin = min_margin
        self.max_debt_to_equity = max_debt_to_equity

    def analyze(self, metrics: FundamentalMetrics) -> SectionScore:
        checks: list[float] = []
        reasons: list[str] = []
        ratios = metrics.as_dict()

        if metrics.pe is not None:
            checks.append(1.0 if metrics.pe <= self.max_pe else -1.0)
            reasons.append(f"P/E={metrics.pe:.2f}")
        if metrics.net_margin is not None:
            checks.append(1.0 if metrics.net_margin >= self.min_margin else -1.0)
            reasons.append(f"حاشیه سود={metrics.net_margin:.2%}")
        if metrics.debt_to_equity is not None:
            checks.append(1.0 if metrics.debt_to_equity <= self.max_debt_to_equity else -1.0)
            reasons.append(f"بدهی به حقوق صاحبان سهام={metrics.debt_to_equity:.2f}")
        if metrics.current_ratio is not None:
            checks.append(1.0 if metrics.current_ratio >= 1.0 else -1.0)
            reasons.append(f"نسبت جاری={metrics.current_ratio:.2f}")
        if metrics.dividend_yield is not None:
            checks.append(1.0 if metrics.dividend_yield > 0 else -1.0)
            reasons.append(f"بازده سود نقدی={metrics.dividend_yield:.2%}")

        if not checks:
            return SectionScore(self.section_name, 0.0, 0.0, {"ratios": ratios, "reasons": [], "data_quality": "missing"})
        score = sum(checks) / len(checks)
        confidence = min(1.0, len(checks) / 4.0)
        return SectionScore(
            self.section_name,
            round(score, 4),
            round(confidence, 4),
            {"ratios": ratios, "reasons": reasons, "data_quality": "partial" if len(checks) < 3 else "usable"},
        )
