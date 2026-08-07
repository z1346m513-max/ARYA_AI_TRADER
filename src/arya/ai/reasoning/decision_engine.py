"""
AI Decision Engine: لایه‌ی پنجم پایپ‌لاین (Scoring Engine -> AI Decision Engine -> Risk Manager).

نسخه‌ی Milestone 1 یک موتور Rule-Based قابل توضیح (Explainable) است: بر اساس
امتیاز کلی، اطمینان و روند اجماع بخش‌ها تصمیم می‌گیرد و دلایل انسانی‌خوان تولید
می‌کند. معماری به‌گونه‌ای است که در آینده می‌توان این کلاس را با یک مدل
یادگیری ماشین (مثلا از src/arya/ai/models و ai/prediction) جایگزین یا ترکیب کرد،
بدون تغییر قرارداد ورودی/خروجی (DecisionEngine.decide).
"""
from __future__ import annotations

from dataclasses import dataclass

from arya.models.analysis_result import SectionScore


@dataclass
class Decision:
    action_score: float          # [-1, 1] - همان overall_score عبوری
    confidence: float            # [0, 1]
    trend_quality: float         # [0, 1]
    reasons: list[str]


class RuleBasedDecisionEngine:
    """موتور تصمیم‌گیری قانون-محور و قابل توضیح."""

    BUY_THRESHOLD = 0.25
    SELL_THRESHOLD = -0.25

    def decide(
        self,
        overall_score: float,
        overall_confidence: float,
        section_scores: list[SectionScore],
    ) -> Decision:
        reasons: list[str] = []

        for s in section_scores:
            if abs(s.score) < 0.1:
                continue
            direction = "صعودی" if s.score > 0 else "نزولی"
            reasons.append(
                f"بخش «{s.section}» سیگنال {direction} با قدرت {abs(s.score):.2f} "
                f"و اطمینان {s.confidence:.2f} می‌دهد."
            )

        if overall_score >= self.BUY_THRESHOLD:
            reasons.append(f"امتیاز کلی ({overall_score:.2f}) بالاتر از آستانه خرید است.")
        elif overall_score <= self.SELL_THRESHOLD:
            reasons.append(f"امتیاز کلی ({overall_score:.2f}) پایین‌تر از آستانه فروش است.")
        else:
            reasons.append(f"امتیاز کلی ({overall_score:.2f}) در محدوده خنثی قرار دارد.")

        # کیفیت روند: ترکیبی از اطمینان کلی و هم‌جهتی بخش‌ها
        agreeing = sum(1 for s in section_scores if s.score * overall_score > 0 and abs(s.score) > 0.05)
        total_active = sum(1 for s in section_scores if abs(s.score) > 0.05) or 1
        trend_quality = round(0.5 * overall_confidence + 0.5 * (agreeing / total_active), 4)

        if not reasons:
            reasons.append("داده کافی برای استخراج دلیل مشخص وجود ندارد.")

        return Decision(
            action_score=overall_score,
            confidence=overall_confidence,
            trend_quality=trend_quality,
            reasons=reasons,
        )
