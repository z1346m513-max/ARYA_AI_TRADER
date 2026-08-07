"""
Scoring Engine: لایه‌ی چهارم پایپ‌لاین (Analysis Engine -> Scoring Engine -> AI Decision Engine).

مسئولیت: ترکیب SectionScoreهای مختلف (تکنیکال، بنیادی، اخبار، کدال، اسمارت‌مانی، ...)
بر اساس وزن‌های تعریف‌شده در configs/weights.yaml (یا پروفایل فعال) و تولید یک
امتیاز کلی + سطح اطمینان کلی. بخش‌هایی که هنوز پیاده‌سازی نشده‌اند (fundamental,
news, ...) با امتیاز خنثی صفر و اطمینان صفر وارد محاسبه می‌شوند تا وزن‌شان به‌طور
غیرمستقیم صرف‌نظر شود، بدون این‌که فرمول کلی به‌هم بریزد.
"""
from __future__ import annotations

from arya.config.settings import Settings
from arya.models.analysis_result import SectionScore


class ScoringEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    def combine(self, section_scores: list[SectionScore]) -> tuple[float, float, list[SectionScore]]:
        """
        خروجی: (overall_score [-1,1], overall_confidence [0,1], لیست section_scores ورودی)
        """
        weights = self.settings.active_weight_profile()
        by_section = {s.section: s for s in section_scores}

        weighted_sum = 0.0
        weight_used = 0.0
        confidence_sum = 0.0

        for section, weight in weights.items():
            s = by_section.get(section)
            if s is None:
                continue  # بخش هنوز پیاده‌سازی نشده -> صرف‌نظر از وزنش
            weighted_sum += s.score * weight
            weight_used += weight
            confidence_sum += s.confidence * weight

        if weight_used == 0:
            return 0.0, 0.0, section_scores

        overall_score = weighted_sum / weight_used
        overall_confidence = confidence_sum / weight_used

        return round(overall_score, 4), round(overall_confidence, 4), section_scores
