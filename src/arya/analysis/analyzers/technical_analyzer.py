"""
Analysis Engine (بخش تکنیکال): لایه‌ی سوم پایپ‌لاین.
لیست IndicatorResult را می‌گیرد و به یک SectionScore واحد ("technical")
تبدیل می‌کند - میانگین وزن‌دار امتیازها + سطح اطمینان بر اساس هم‌جهتی اندیکاتورها.

سایر Analyzerها (fundamental, news, codal, smart_money, ...) در فازهای بعدی
با همین الگو (خروجی SectionScore) اضافه می‌شوند تا Scoring Engine بدون تغییر
بتواند همه را ترکیب کند.
"""
from __future__ import annotations

from arya.models.analysis_result import IndicatorResult, SectionScore


class TechnicalAnalyzer:
    section_name = "technical"

    def analyze(self, indicator_results: list[IndicatorResult]) -> SectionScore:
        if not indicator_results:
            return SectionScore(section=self.section_name, score=0.0, confidence=0.0, details={})

        total_weight = sum(r.weight for r in indicator_results) or 1.0
        weighted_score = sum(r.score * r.weight for r in indicator_results) / total_weight

        # اطمینان = میزان هم‌جهت بودن اندیکاتورها (کمتر پراکنده = اطمینان بیشتر)
        signs = [1 if r.score > 0.05 else (-1 if r.score < -0.05 else 0) for r in indicator_results]
        agreement = abs(sum(signs)) / len(signs) if signs else 0.0

        all_alerts = [a for r in indicator_results for a in r.triggered_alerts]

        details = {
            "indicators": {r.name: {"value": r.value, "score": round(r.score, 3)} for r in indicator_results},
            "alerts": all_alerts,
        }

        return SectionScore(
            section=self.section_name,
            score=round(weighted_score, 4),
            confidence=round(agreement, 4),
            details=details,
        )
