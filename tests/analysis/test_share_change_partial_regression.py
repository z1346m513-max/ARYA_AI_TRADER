"""تست رگرسیون CR-20261029-001 — دادهٔ partial هرگز امتیاز معاملاتی معتبر تولید نمی‌کند.

زمینه (بازبینی مالک پیش از ادغام): نسخهٔ قبلی Analyzer به partial ضریب اطمینان 0.5 می‌داد
و می‌توانست از متریک‌های ناقص سیگنال بسازد. این تست‌ها رفتار جدید را قفل می‌کنند:
هر data_quality غیر از "usable" باید امتیاز=0، اطمینان=0 و دلیل صریح بدهد —
حتی اگر مقادیر متریک‌ها به‌طور مخرب پر شده باشند.
"""
from __future__ import annotations

from arya.analysis.analyzers.share_change_analyzer import ShareChangeAnalyzer
from arya.models.shareholders import ShareholderCountPoint, ShareholderFlowMetrics
from arya.providers.shareholders.mock_provider import MockShareholderProvider


def _metrics(data_quality: str, **overrides) -> ShareholderFlowMetrics:
    """مدل با مقادیرِ عمداً «قابل‌امتیازدهی» — اگر گیت کار نکند، Analyzer امتیاز خواهد ساخت."""
    base = dict(
        ticker="TEST",
        shareholder_count_series=(ShareholderCountPoint("2026-10-20", 100_000),),
        shareholder_count_change_pct=-9.9,       # آستانهٔ تمرکز را رد می‌کند → سیگنال 1.0
        individual_avg_buy_value=3.0e8,
        individual_avg_sell_value=1.0e8,          # نسبت 3.0 → سیگنال 1.0
        legal_buy_share=0.45,
        legal_net_buy_value=7.0e9,                # حقوقی مثبت → سیگنال 1.0
        data_quality=data_quality,
        source="test:poisoned-values",
    )
    base.update(overrides)
    return ShareholderFlowMetrics(**base)


def test_partial_with_scoreable_values_is_zeroed():
    s = ShareChangeAnalyzer().analyze(_metrics("partial"))
    assert s.score == 0.0
    assert s.confidence == 0.0
    assert s.details["data_quality"] == "partial"
    assert any("partial" in r for r in s.details["reasons"])
    # متریک‌های مسموم نباید در مسیر امتیاز مصرف شده باشند — فقط گزارش شده‌اند
    assert s.details["metrics"]["legal_net_buy_value"] == 7.0e9


def test_missing_has_explicit_reason():
    s = ShareChangeAnalyzer().analyze(_metrics("missing"))
    assert s.score == 0.0
    assert s.confidence == 0.0
    assert s.details["data_quality"] == "missing"
    assert s.details["reasons"]  # دلیل صریح به‌جای reasons خالی قدیمی


def test_unknown_quality_state_is_blocked():
    s = ShareChangeAnalyzer().analyze(_metrics("degraded"))
    assert s.score == 0.0
    assert s.confidence == 0.0
    assert any("degraded" in r for r in s.details["reasons"])


def test_usable_still_scores_regression_guard():
    """حفاظ در برابر بسته‌شدن بیش‌ازحد: usable باید همچنان امتیاز بدهد."""
    p = MockShareholderProvider()
    s = ShareChangeAnalyzer().analyze(p.fetch_shareholder_flow("ACCUM"))
    assert s.score > 0
    assert s.confidence > 0
