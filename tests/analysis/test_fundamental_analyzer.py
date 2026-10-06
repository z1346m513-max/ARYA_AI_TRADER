"""
تست‌های FundamentalAnalyzer با ۱۹ نسبت مالی.

موارد پوشش‌داده‌شده:
- analyze(metrics) قدیمی همچنان کار می‌کند (backward compatibility)
- analyze_financial_data(data) جدید با داده‌ی کامل
- داده‌ی کامل: امتیاز مثبت و اطمینان بالا
- داده‌ی بد: امتیاز منفی
- داده‌ی ناقص: امتیاز ۰، بدون امتیاز مثبت جعلی
- تمام ۱۹ نسبت در details موجودند
- thresholds قابل تنظیم هستند
- data_quality بر اساس تعداد نسبت‌های امتیازدهی‌شده
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest

from arya.analysis.analyzers.fundamental_analyzer import (
    FundamentalAnalyzer,
    FundamentalThresholds,
)
from arya.fundamental.models import FinancialData
from arya.models.fundamentals import FundamentalMetrics


# ─── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def full_data():
    """داده‌ی بنیادی کامل و سالم."""
    return FinancialData(
        # بازار
        market_price=10000.0,
        shares_outstanding=1_000_000.0,
        market_cap=10_000_000_000.0,
        # صورت سود و زیان
        revenue=50_000_000_000.0,
        cost_of_goods_sold=30_000_000_000.0,
        gross_profit=20_000_000_000.0,
        operating_income=8_000_000_000.0,
        net_income=6_000_000_000.0,
        eps=6000.0,
        interest_expense=1_000_000_000.0,
        depreciation=2_000_000_000.0,
        operating_cash_flow=7_000_000_000.0,
        cash_flow_per_share=7000.0,
        # ترازنامه
        total_assets=80_000_000_000.0,
        total_liabilities=30_000_000_000.0,
        equity=50_000_000_000.0,
        current_assets=20_000_000_000.0,
        current_liabilities=10_000_000_000.0,
        inventory=5_000_000_000.0,
        receivables=3_000_000_000.0,
        fixed_assets=40_000_000_000.0,
        cash=4_000_000_000.0,
        debt=15_000_000_000.0,
        book_value_per_share=50000.0,
        # رشد و تقسیم سود
        earnings_growth_rate_percent=20.0,
        dividend_per_share=2000.0,
        # میانگین‌ها
        avg_total_assets=78_000_000_000.0,
        avg_equity=48_000_000_000.0,
        avg_inventory=4_500_000_000.0,
        avg_receivables=2_800_000_000.0,
        avg_fixed_assets=38_000_000_000.0,
    )


@pytest.fixture
def bad_data():
    """داده‌ی بنیادی ضعیف: P/E بالا، حاشیه سود پایین، بدهی بالا."""
    return FinancialData(
        market_price=50000.0,
        shares_outstanding=1_000_000.0,
        revenue=10_000_000_000.0,
        cost_of_goods_sold=9_500_000_000.0,
        net_income=100_000_000.0,
        eps=100.0,
        total_assets=20_000_000_000.0,
        equity=5_000_000_000.0,
        current_assets=3_000_000_000.0,
        current_liabilities=5_000_000_000.0,
        inventory=2_000_000_000.0,
        debt=12_000_000_000.0,
        total_liabilities=15_000_000_000.0,
        operating_income=500_000_000.0,
        interest_expense=800_000_000.0,
    )


# ─── Backward Compatibility Tests ──────────────────────────

def test_analyze_with_metrics_still_works():
    """متد قدیمی analyze(metrics) همچنان باید کار کند."""
    metrics = FundamentalMetrics(
        eps=10, market_price=100, book_value_per_share=50,
        dividend_per_share=5, revenue=1_000, net_income=100,
        debt=500, equity=500, current_assets=300, current_liabilities=200,
    )
    result = FundamentalAnalyzer().analyze(metrics)
    assert result.section == "fundamental"
    assert -1 <= result.score <= 1
    assert 0 <= result.confidence <= 1


def test_analyze_with_empty_metrics_gives_zero_confidence():
    """داده‌ی خالی باید اطمینان ۰ بدهد."""
    result = FundamentalAnalyzer().analyze(FundamentalMetrics())
    assert result.confidence == 0.0


def test_old_test_data_quality():
    """تست قدیمی data_quality هنوز باید کار کند."""
    metrics = FundamentalMetrics(
        eps=10, market_price=100, book_value_per_share=50,
        dividend_per_share=5, revenue=1_000, net_income=100,
        debt=500, equity=500, current_assets=300, current_liabilities=200,
    )
    result = FundamentalAnalyzer().analyze(metrics)
    assert result.confidence > 0
    assert result.details["data_quality"] in ("usable", "partial")


# ─── New analyze_financial_data Tests ────────────────────────

def test_analyze_financial_data_with_full_data(full_data):
    """داده‌ی کامل باید امتیاز مثبت و اطمینان بالا بدهد."""
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze_financial_data(full_data)

    assert result.section == "fundamental"
    assert result.score > 0  # امتیاز مثبت
    assert result.confidence > 0.5  # اطمینان بالا
    assert result.details["data_quality"] == "usable"


def test_analyze_financial_data_with_bad_data(bad_data):
    """داده‌ی ضعیف باید امتیاز منفی بدهد."""
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze_financial_data(bad_data)

    assert result.score < 0  # اطعمیاز منفی


def test_analyze_financial_data_with_empty_data():
    """داده‌ی خالی نباید امتیاز مثبت جعلی تولید کند."""
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze_financial_data(FinancialData())

    assert result.score == 0.0
    assert result.confidence == 0.0
    assert result.details["data_quality"] == "missing"


def test_all_19_ratios_in_details(full_data):
    """تمام ۱۹ نسبت باید در details موجود باشند."""
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze_financial_data(full_data)

    ratios = result.details["ratios"]
    expected_keys = {
        "pe", "pb", "ps", "pcf", "peg",
        "gross_margin", "net_margin", "roe", "roa",
        "current_ratio", "quick_ratio", "cash_ratio",
        "debt_to_equity", "debt_to_asset", "interest_coverage",
        "inventory_turnover", "fixed_asset_turnover", "receivables_period",
        "payout_ratio",
    }
    assert set(ratios.keys()) == expected_keys
    # هر نسبت باید حداقل key و status داشته باشد
    for key, ratio in ratios.items():
        assert "key" in ratio
        assert "status" in ratio
        assert "value" in ratio


def test_scored_keys_separated_from_informational(full_data):
    """نسبت‌های امتیازدهی‌شده باید از اطلاعاتی جدا باشند."""
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze_financial_data(full_data)

    scored = result.details["scored_ratio_keys"]
    # ۹ نسبت امتیازدهی‌شده
    assert len(scored) == 9
    assert "pe" in scored
    assert "roe" in scored
    assert "debt_to_equity" in scored
    # نسبت‌های اطلاعاتی نباید در scored باشند
    assert "pb" not in scored  # اطلاعاتی
    assert "inventory_turnover" not in scored  # اطلاعاتی


def test_unavailable_ratios_tracked(full_data):
    """نسبت‌های UNAVAILABLE باید در details ثبت شوند."""
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze_financial_data(full_data)

    unavailable = result.details["unavailable_ratio_keys"]
    # با داده‌ی کامل نباید unavailable باشد
    assert len(unavailable) == 0


def test_partial_data_has_unavailable_ratios():
    """داده‌ی ناقص باید نسبت‌های UNAVAILABLE داشته باشد."""
    data = FinancialData(
        market_price=10000.0, eps=5000.0,
        revenue=50_000_000.0, net_income=5_000_000.0,
        equity=50_000_000.0, total_assets=80_000_000.0,
        current_assets=20_000_000.0, current_liabilities=10_000_000.0,
        debt=15_000_000.0, operating_income=8_000_000.0,
        interest_expense=1_000_000.0,
    )
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze_financial_data(data)

    unavailable = result.details["unavailable_ratio_keys"]
    # روابطی که نیاز به داده‌ی اضافی دارند باید unavailable باشند
    assert "peg" in unavailable  # earnings_growth_rate missing
    assert "pcf" in unavailable  # cash_flow_per_share missing
    # quick_ratio با inventory ناچیز = OK (استفاده از 0 محافظه‌کارانه)
    # اما pcf و peg باید unavailable باشند


def test_custom_thresholds():
    """thresholds قابل تنظیم باید کار کنند."""
    thresholds = FundamentalThresholds(
        max_pe=5.0,
        min_roe=0.20,
        min_current_ratio=2.0,
    )
    analyzer = FundamentalAnalyzer(thresholds=thresholds)
    assert analyzer.thresholds.max_pe == 5.0
    assert analyzer.thresholds.min_roe == 0.20


def test_data_quality_levels():
    """data_quality باید بر اساس تعداد نسبت‌های امتیازدهی‌شده تغییر کند."""
    # داده‌ی کامل: usable
    full = FinancialData(
        market_price=10000.0, eps=6000.0,
        revenue=50_000_000_000.0, net_income=6_000_000_000.0,
        equity=50_000_000_000.0, total_assets=80_000_000_000.0,
        current_assets=20_000_000_000.0, current_liabilities=10_000_000_000.0,
        debt=15_000_000_000.0, operating_income=8_000_000_000.0,
        interest_expense=1_000_000_000.0,
        inventory=5_000_000_000.0, receivables=3_000_000_000.0,
        cost_of_goods_sold=30_000_000_000.0,
        avg_equity=48_000_000_000.0, avg_total_assets=78_000_000_000.0,
        avg_inventory=4_500_000_000.0, avg_fixed_assets=38_000_000_000.0,
        avg_receivables=2_800_000_000.0,
        fixed_assets=40_000_000_000.0,
    )
    result = FundamentalAnalyzer().analyze_financial_data(full)
    assert result.details["data_quality"] == "usable"


def test_reasons_contain_thresholds(full_data):
    """reasons باید شامل آستانه‌ها باشند."""
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze_financial_data(full_data)

    reasons = result.details["reasons"]
    assert len(reasons) > 0
    # باید حداقل یکی شامل P/E باشد
    assert any("P/E" in r for r in reasons)


def test_negative_eps_in_details(bad_data):
    """اگر EPS منفی باشد، باید در not_meaningful_keys ثبت شود."""
    data = FinancialData(
        market_price=5000.0, eps=-200.0,
        revenue=10_000_000.0, net_income=-200_000.0,
    )
    analyzer = FundamentalAnalyzer()
    result = analyzer.analyze_financial_data(data)

    not_meaningful = result.details["not_meaningful_ratio_keys"]
    assert "pe" in not_meaningful
    assert "payout_ratio" in not_meaningful


def test_backward_compat_old_constructor_params():
    """پارامترهای قدعیق سازنده باید همچنان کار کنند."""
    analyzer = FundamentalAnalyzer(
        max_pe=20.0, min_margin=0.05, max_debt_to_equity=3.0,
    )
    assert analyzer.thresholds.max_pe == 20.0
    assert analyzer.thresholds.min_net_margin == 0.05
    assert analyzer.thresholds.max_debt_to_equity == 3.0


def test_thresholds_dataclass_is_frozen():
    """FundamentalThresholds باید immutable باشد."""
    thresholds = FundamentalThresholds()
    with pytest.raises(Exception):
        thresholds.max_pe = 100.0
