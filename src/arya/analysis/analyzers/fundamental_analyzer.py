"""تحلیل بنیادی محافظه‌کارانه؛ دادهٔ ناقص امتیاز مثبت جعلی تولید نمی‌کند.

این نسخه از تمام ۱۹ نسبت مالی ماژول arya.fundamental استفاده می‌کند، اما فقط
۹ نسبت تفسیرپذیر و عمومی را امتیازدهی می‌کند. بقیه به‌صورت اطلاعاتی در details
قرار می‌گیرند تا در دسترس باشند ولی در امتیاز نهایی تاثیر نداشته باشند.

سازگار با نسخه‌ی قبلی: متد analyze(metrics: FundamentalMetrics) همچنان کار می‌کند
و از طریق bridge به مسیر ۱۹ نسبتی هدایت می‌شود.
"""
from __future__ import annotations

from dataclasses import dataclass

from arya.fundamental.models import FinancialData
from arya.fundamental.ratios import calculate_all_ratios, RatioResult
from arya.models.analysis_result import SectionScore
from arya.models.fundamentals import FundamentalMetrics


@dataclass(frozen=True)
class FundamentalThresholds:
    """آستانه‌های قابل‌تنظیم برای امتیازدهی نسبت‌های بنیادی."""

    max_pe: float = 15.0
    min_net_margin: float = 0.0
    min_roe: float = 0.10
    min_roa: float = 0.03
    min_current_ratio: float = 1.0
    min_quick_ratio: float = 0.7
    max_debt_to_equity: float = 2.0
    max_debt_to_asset: float = 0.7
    min_interest_coverage: float = 2.0


class FundamentalAnalyzer:
    """تحلیلگر بنیادی با ۱۹ نسبت مالی و امتیازدهی محافظه‌کارانه."""

    section_name = "fundamental"

    def __init__(
        self,
        max_pe: float = 15.0,
        min_margin: float = 0.0,
        max_debt_to_equity: float = 2.0,
        thresholds: FundamentalThresholds | None = None,
    ):
        # سازگاری با نسخه‌ی قبلی: اگر thresholds داده نشد، از پارامترهای قدیمی استفاده کن
        if thresholds is not None:
            self.thresholds = thresholds
        else:
            self.thresholds = FundamentalThresholds(
                max_pe=max_pe,
                min_net_margin=min_margin,
                max_debt_to_equity=max_debt_to_equity,
            )

    # ─── رابط عمومی ───

    def analyze(self, metrics: FundamentalMetrics) -> SectionScore:
        """
        تحلیل با FundamentalMetrics (رابط قدیمی).

        این متد برای سازگاری با نسخه‌ی قبلی حفظ شده است. داده‌ی metrics را
        از طریق FinancialData.from_metrics به مسیر ۱۹ نسبتی هدایت می‌کند.
        """
        data = FinancialData.from_metrics(metrics)
        return self.analyze_financial_data(data)

    def analyze_financial_data(self, data: FinancialData) -> SectionScore:
        """
        تحلیل با FinancialData و ۱۹ نسبت مالی.

        ۹ نسبت تفسیرپذیر امتیازدهی می‌شوند:
        P/E، حاشیه سود خالص، ROE، ROA، نسبت جاری، نسبت آنی،
        بدهی به حقوق صاحبان سهام، بدهی به دارایی، پوشش هزینه بهره.

        بقیه ۱۰ نسبت (P/BV، P/S، P/CF، PEG، حاشیه سود ناخالص، گردش موجودی،
        گردش دارایی ثابت، دوره وصول مطالبات، نسبت پرداخت سود) به‌صورت اطلاعاتی
        در details قرار می‌گیرند ولی در امتیاز نهایی تاثیر ندارند.

        Args:
            data: داده‌ی بنیادی کامل.

        Returns:
            SectionScore شامل امتیاز، اطمینان و جزئیات تمام ۱۹ نسبت.
        """
        ratios = calculate_all_ratios(data)

        checks: list[float] = []
        reasons: list[str] = []
        scored_keys: list[str] = []
        unavailable_keys: list[str] = []
        not_meaningful_keys: list[str] = []

        for key, result in ratios.items():
            if result.status == "UNAVAILABLE":
                unavailable_keys.append(key)
                continue
            if result.status == "NOT_MEANINGFUL":
                not_meaningful_keys.append(key)
                # برای مواردی مثل P/E منفی، یک دلیل منفی ثبت کن
                if key == "pe" or key == "peg":
                    reasons.append(f"{result.name}: {result.warnings[0] if result.warnings else 'معنا ندارد'}")
                continue
            # status == "OK"
            scored = self._score_ratio(key, result, checks, reasons)
            if scored:
                scored_keys.append(key)

        # محاسبه‌ی امتیاز نهایی
        if not checks:
            return SectionScore(
                self.section_name,
                0.0,
                0.0,
                {
                    "ratios": {k: r.as_dict() for k, r in ratios.items()},
                    "reasons": reasons,
                    "scored_ratio_keys": scored_keys,
                    "unavailable_ratio_keys": unavailable_keys,
                    "not_meaningful_ratio_keys": not_meaningful_keys,
                    "data_quality": "missing",
                },
            )

        score = sum(checks) / len(checks)
        # اطمینان بر اساس تعداد نسبت‌های امتیازدهی‌شده (نه ۱۹)
        confidence = min(1.0, len(checks) / 6.0)

        data_quality = "missing"
        if len(checks) >= 6:
            data_quality = "usable"
        elif len(checks) >= 3:
            data_quality = "partial"
        else:
            data_quality = "sparse"

        return SectionScore(
            self.section_name,
            round(score, 4),
            round(confidence, 4),
            {
                "ratios": {k: r.as_dict() for k, r in ratios.items()},
                "reasons": reasons,
                "scored_ratio_keys": scored_keys,
                "unavailable_ratio_keys": unavailable_keys,
                "not_meaningful_ratio_keys": not_meaningful_keys,
                "data_quality": data_quality,
            },
        )

    # ─── امتیازدهی نسبت‌ها ───

    def _score_ratio(
        self,
        key: str,
        result: RatioResult,
        checks: list[float],
        reasons: list[str],
    ) -> bool:
        """
        یک نسبت OK را امتیازدهی می‌کند (۱.۰ = عبور، -۱.۰ = رد).
        
        Returns:
            True اگر نسبت امتیازدهی شد، False اگر اطلاعاتی بود.
        """
        t = self.thresholds
        value = result.value
        if value is None:
            return

        passed = False
        threshold_desc = ""

        if key == "pe":
            passed = value <= t.max_pe
            threshold_desc = f"P/E={value:.2f} (آستانه: {t.max_pe})"
        elif key == "net_margin":
            passed = value >= t.min_net_margin
            threshold_desc = f"حاشیه سود={value:.2%} (حداقل: {t.min_net_margin:.0%})"
        elif key == "roe":
            passed = value >= t.min_roe
            threshold_desc = f"ROE={value:.2%} (حداقل: {t.min_roe:.0%})"
        elif key == "roa":
            passed = value >= t.min_roa
            threshold_desc = f"ROA={value:.2%} (حداقل: {t.min_roa:.0%})"
        elif key == "current_ratio":
            passed = value >= t.min_current_ratio
            threshold_desc = f"نسبت جاری={value:.2f} (حداقل: {t.min_current_ratio})"
        elif key == "quick_ratio":
            passed = value >= t.min_quick_ratio
            threshold_desc = f"نسبت آنی={value:.2f} (حداقل: {t.min_quick_ratio})"
        elif key == "debt_to_equity":
            passed = value <= t.max_debt_to_equity
            threshold_desc = f"بدهی/حقوق صاحبان سهام={value:.2f} (حداکثر: {t.max_debt_to_equity})"
        elif key == "debt_to_asset":
            passed = value <= t.max_debt_to_asset
            threshold_desc = f"بدهی/دارایی={value:.2%} (حداکثر: {t.max_debt_to_asset:.0%})"
        elif key == "interest_coverage":
            passed = value >= t.min_interest_coverage
            threshold_desc = f"پوشش بهره={value:.2f} (حداقل: {t.min_interest_coverage})"
        else:
            # نسبت‌های اطلاعاتی: امتیازدهی نمی‌شوند
            return False

        checks.append(1.0 if passed else -1.0)
        status_str = "عبور" if passed else "رد"
        reasons.append(f"{threshold_desc} — {status_str}")
        return True
