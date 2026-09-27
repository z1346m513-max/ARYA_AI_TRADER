"""
AI Decision Engine: Rule-Based and explainable decision layer.

Presentation language is configurable; internal action values remain stable.
"""
from __future__ import annotations

from dataclasses import dataclass

from arya.dashboard.i18n import translate_section
from arya.models.analysis_result import SectionScore


@dataclass
class Decision:
    action_score: float
    confidence: float
    trend_quality: float
    reasons: list[str]


class RuleBasedDecisionEngine:
    """موتور تصمیم‌گیری قانون‌محور و قابل توضیح."""

    BUY_THRESHOLD = 0.25
    SELL_THRESHOLD = -0.25

    def decide(
        self,
        overall_score: float,
        overall_confidence: float,
        section_scores: list[SectionScore],
        language: str = "fa",
    ) -> Decision:
        reasons: list[str] = []

        for section in section_scores:
            if abs(section.score) < 0.1:
                continue
            direction = "صعودی" if section.score > 0 else "نزولی"
            if language == "en":
                direction = "bullish" if section.score > 0 else "bearish"
            reasons.append(
                f"بخش «{translate_section(section.section, language)}» "
                f"{('سیگنال ' + direction) if language != 'en' else ('signal: ' + direction)} "
                f"با قدرت {abs(section.score):.2f} "
                f"و اطمینان {section.confidence:.2f} "
                f"{'می‌دهد.' if language != 'en' else 'given.'}"
            )

        if overall_score >= self.BUY_THRESHOLD:
            reasons.append(
                f"امتیاز کلی ({overall_score:.2f}) "
                f"{'بالاتر از آستانه خرید است.' if language != 'en' else 'is above the buy threshold.'}"
            )
        elif overall_score <= self.SELL_THRESHOLD:
            reasons.append(
                f"امتیاز کلی ({overall_score:.2f}) "
                f"{'پایین‌تر از آستانه فروش است.' if language != 'en' else 'is below the sell threshold.'}"
            )
        else:
            reasons.append(
                f"امتیاز کلی ({overall_score:.2f}) "
                f"{'در محدوده خنثی قرار دارد.' if language != 'en' else 'is in the neutral range.'}"
            )

        agreeing = sum(
            1
            for section in section_scores
            if section.score * overall_score > 0 and abs(section.score) > 0.05
        )
        total_active = (
            sum(1 for section in section_scores if abs(section.score) > 0.05) or 1
        )
        trend_quality = round(
            0.5 * overall_confidence + 0.5 * (agreeing / total_active),
            4,
        )

        if not reasons:
            reasons.append(
                "داده کافی برای استخراج دلیل مشخص وجود ندارد."
                if language != "en"
                else "There is not enough data to produce a specific reason."
            )

        return Decision(
            action_score=overall_score,
            confidence=overall_confidence,
            trend_quality=trend_quality,
            reasons=reasons,
        )
