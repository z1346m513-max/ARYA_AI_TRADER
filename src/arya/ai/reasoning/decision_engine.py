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

            if language == "en":
                section_name = translate_section(section.section, "en")
                direction = "bullish" if section.score > 0 else "bearish"
                reasons.append(
                    f"Section '{section_name}' gives a {direction} signal "
                    f"with strength {abs(section.score):.2f} "
                    f"and confidence {section.confidence:.2f}."
                )
            else:
                section_name = translate_section(section.section, "fa")
                direction = "صعودی" if section.score > 0 else "نزولی"
                reasons.append(
                    f"بخش «{section_name}» سیگنال {direction} "
                    f"با قدرت {abs(section.score):.2f} "
                    f"و اطمینان {section.confidence:.2f} می‌دهد."
                )

        if overall_score >= self.BUY_THRESHOLD:
            reasons.append(
                f"Overall score ({overall_score:.2f}) "
                f"{'is above the buy threshold.' if language == 'en' else 'بالاتر از آستانه خرید است.'}"
                if language == "en"
                else f"امتیاز کلی ({overall_score:.2f}) بالاتر از آستانه خرید است."
            )
        elif overall_score <= self.SELL_THRESHOLD:
            reasons.append(
                f"Overall score ({overall_score:.2f}) is below the sell threshold."
                if language == "en"
                else f"امتیاز کلی ({overall_score:.2f}) پایین‌تر از آستانه فروش است."
            )
        else:
            reasons.append(
                f"Overall score ({overall_score:.2f}) is in the neutral range."
                if language == "en"
                else f"امتیاز کلی ({overall_score:.2f}) در محدوده خنثی قرار دارد."
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
                "There is not enough data to produce a specific reason."
                if language == "en"
                else "داده کافی برای استخراج دلیل مشخص وجود ندارد."
            )

        return Decision(
            action_score=overall_score,
            confidence=overall_confidence,
            trend_quality=trend_quality,
            reasons=reasons,
        )
