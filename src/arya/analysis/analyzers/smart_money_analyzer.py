"""
تحلیل پول هوشمند از حقیقی/حقوقی (TSETMC ClientType).

منطق ساده و محافظه‌کارانه برای بازار ایران:
- ورود خالص حقوقی → امتیاز مثبت
- خروج خالص حقوقی (و ورود سنگین حقیقی) → امتیاز منفی یا خنثی محتاط
"""
from __future__ import annotations

from arya.models.analysis_result import SectionScore
from arya.providers.market.client_type_provider import ClientTypeSnapshot


class SmartMoneyAnalyzer:
    section_name = "smart_money"

    def analyze(self, snap: ClientTypeSnapshot) -> SectionScore:
        net_n = snap.net_institutional_volume
        net_i = snap.net_individual_volume
        buy_n = snap.buy_institutional_volume or 0.0
        sell_n = snap.sell_institutional_volume or 0.0
        total_n = buy_n + sell_n

        reasons: list[str] = []
        score = 0.0
        confidence = 0.25

        if net_n is not None and total_n > 0:
            # نسبت خالص حقوقی به کل گردش حقوقی [-1, 1]
            ratio = max(-1.0, min(1.0, net_n / total_n))
            score = round(ratio * 0.7, 4)  # سقف محافظه‌کارانه
            confidence = min(0.65, 0.3 + abs(ratio) * 0.35)

            if net_n > 0:
                reasons.append(
                    f"حقوقی خالص خریدار: {net_n:+,.0f} سهم (نسبت {ratio:+.0%})"
                )
            elif net_n < 0:
                reasons.append(
                    f"حقوقی خالص فروشنده: {net_n:+,.0f} سهم (نسبت {ratio:+.0%})"
                )
            else:
                reasons.append("خالص حقوقی نزدیک صفر")

        if net_i is not None:
            if net_i > 0 and (net_n is not None and net_n < 0):
                reasons.append(
                    f"حقیقی خالص خرید در برابر فروش حقوقی: {net_i:+,.0f}"
                )
                # در بورس ایران این ترکیب اغلب توزیع حقوقی است → کمی منفی‌تر
                score = round(max(-0.85, score - 0.15), 4)
            elif net_i < 0 and (net_n is not None and net_n > 0):
                reasons.append("حقوقی خریدار و حقیقی فروشنده (جابه‌جایی به حقوقی)")
                score = round(min(0.85, score + 0.1), 4)

        if not reasons:
            reasons.append("داده حقیقی/حقوقی ناکافی")
            confidence = 0.1

        return SectionScore(
            self.section_name,
            score,
            round(confidence, 4),
            {
                "reasons": reasons,
                "net_institutional": net_n,
                "net_individual": net_i,
                "data_quality": "client_type",
            },
        )
