"""
تست‌های نسبت‌های مالی.

موارد پوشش‌داده‌شده:
- داده‌ی کامل: همه نسبت‌ها عدد درست بدهند
- تقسیم بر صفر: None و NOT_MEANINGFUL
- داده‌ی ناقص: UNAVAILABLE
- EPS منفی: P/E = NOT_MEANINGFUL
- PEG با رشد صفر یا منفی: NOT_MEANINGFUL
- پوشش هزینه بهره با بهره صفر: NOT_MEANINGFUL
- محاسبه از مسیر per-share و market-cap
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest

from arya.fundamental.models import FinancialData
from arya.fundamental.ratios import (
    RatioResult,
    calculate_all_ratios,
    price_to_earnings,
    price_to_book,
    price_to_sales,
    price_to_cash_flow,
    peg_ratio,
    gross_profit_margin,
    net_profit_margin,
    return_on_equity,
    return_on_assets,
    current_ratio,
    quick_ratio,
    cash_ratio,
    debt_to_equity,
    debt_to_asset,
    interest_coverage,
    inventory_turnover,
    fixed_asset_turnover,
    receivables_collection_period,
    dividend_payout_ratio,
)


# ─── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def full_data():
    """داده‌ی کامل با تمام فیلدهای پر شده."""
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
def empty_data():
    """داده‌ی خالی - هیچ فیلدی پر نشده."""
    return FinancialData()


@pytest.fixture
def negative_eps_data():
    """داده‌ی با EPS منفی."""
    return FinancialData(
        market_price=5000.0,
        eps=-200.0,
        net_income=-200_000_000.0,
        revenue=10_000_000_000.0,
    )


# ─── Market Value Ratios Tests ─────────────────────────────

def test_pe_with_full_data(full_data):
    result = price_to_earnings(full_data)
    assert result.status == "OK"
    assert result.value is not None
    assert result.value == pytest.approx(10000.0 / 6000.0)


def test_pe_with_negative_eps(negative_eps_data):
    result = price_to_earnings(negative_eps_data)
    assert result.status == "NOT_MEANINGFUL"
    assert result.value is None
    assert any("EPS" in w for w in result.warnings)


def test_pe_with_empty_data(empty_data):
    result = price_to_earnings(empty_data)
    assert result.status == "UNAVAILABLE"
    assert result.value is None


def test_pb_per_share_path(full_data):
    result = price_to_book(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(10000.0 / 50000.0)


def test_pb_market_cap_path():
    """P/BV از مسیر market_cap / equity محاسبه شود."""
    data = FinancialData(
        market_price=10000.0,
        shares_outstanding=1_000_000.0,
        equity=8_000_000_000.0,
    )
    result = price_to_book(data)
    assert result.status == "OK"
    expected = (10000.0 * 1_000_000) / 8_000_000_000.0
    assert result.value == pytest.approx(expected)


def test_pb_with_empty_data(empty_data):
    result = price_to_book(empty_data)
    assert result.status == "UNAVAILABLE"


def test_ps_per_share_path(full_data):
    result = price_to_sales(full_data)
    assert result.status == "OK"
    # price / (revenue / shares) = 10000 / (50B / 1M) = 10000 / 50000 = 0.2
    sales_per_share = 50_000_000_000.0 / 1_000_000.0
    assert result.value == pytest.approx(10000.0 / sales_per_share)


def test_ps_market_cap_path():
    data = FinancialData(
        market_price=10000.0,
        shares_outstanding=1_000_000.0,
        revenue=5_000_000_000.0,
    )
    result = price_to_sales(data)
    assert result.status == "OK"
    mc = 10000.0 * 1_000_000
    assert result.value == pytest.approx(mc / 5_000_000_000.0)


def test_pcf_per_share_path(full_data):
    result = price_to_cash_flow(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(10000.0 / 7000.0)


def test_pcf_market_cap_path():
    data = FinancialData(
        market_price=10000.0,
        shares_outstanding=1_000_000.0,
        operating_cash_flow=5_000_000_000.0,
    )
    result = price_to_cash_flow(data)
    assert result.status == "OK"
    mc = 10000.0 * 1_000_000
    assert result.value == pytest.approx(mc / 5_000_000_000.0)


def test_peg_with_full_data(full_data):
    result = peg_ratio(full_data)
    assert result.status == "OK"
    # P/E = 10000/6000 = 1.667, growth = 20
    pe = 10000.0 / 6000.0
    assert result.value == pytest.approx(pe / 20.0)


def test_peg_with_zero_growth():
    data = FinancialData(
        market_price=10000.0, eps=6000.0,
        earnings_growth_rate_percent=0.0,
    )
    result = peg_ratio(data)
    assert result.status == "NOT_MEANINGFUL"
    assert result.value is None


def test_peg_with_negative_growth():
    data = FinancialData(
        market_price=10000.0, eps=6000.0,
        earnings_growth_rate_percent=-5.0,
    )
    result = peg_ratio(data)
    assert result.status == "NOT_MEANINGFUL"


def test_peg_without_growth_rate():
    data = FinancialData(market_price=10000.0, eps=6000.0)
    result = peg_ratio(data)
    assert result.status == "UNAVAILABLE"


# ─── Profitability Tests ───────────────────────────────────

def test_gross_profit_margin(full_data):
    result = gross_profit_margin(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(20_000_000_000.0 / 50_000_000_000.0)


def test_gross_profit_margin_from_cogs():
    """اگر gross_profit نباشد، از revenue - COGS محاسبه شود."""
    data = FinancialData(
        revenue=100.0, cost_of_goods_sold=60.0,
    )
    result = gross_profit_margin(data)
    assert result.status == "OK"
    assert result.value == pytest.approx(40.0 / 100.0)


def test_net_profit_margin(full_data):
    result = net_profit_margin(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(6_000_000_000.0 / 50_000_000_000.0)


def test_roe_with_avg(full_data):
    result = return_on_equity(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(6_000_000_000.0 / 48_000_000_000.0)
    assert len(result.warnings) == 0  # میانگین موجود است


def test_roe_without_avg():
    data = FinancialData(
        net_income=6_000_000.0, equity=50_000_000.0,
    )
    result = return_on_equity(data)
    assert result.status == "OK"
    assert result.value == pytest.approx(6_000_000.0 / 50_000_000.0)
    assert any("میانگین" in w for w in result.warnings)


def test_roa_with_avg(full_data):
    result = return_on_assets(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(6_000_000_000.0 / 78_000_000_000.0)


def test_roa_without_avg():
    data = FinancialData(
        net_income=6_000_000.0, total_assets=80_000_000.0,
    )
    result = return_on_assets(data)
    assert result.status == "OK"
    assert result.value == pytest.approx(6_000_000.0 / 80_000_000.0)
    assert any("میانگین" in w for w in result.warnings)


# ─── Liquidity Tests ──────────────────────────────────────

def test_current_ratio(full_data):
    result = current_ratio(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(20_000_000_000.0 / 10_000_000_000.0)


def test_quick_ratio(full_data):
    result = quick_ratio(full_data)
    assert result.status == "OK"
    expected = (20_000_000_000.0 - 5_000_000_000.0) / 10_000_000_000.0
    assert result.value == pytest.approx(expected)


def test_quick_ratio_without_inventory():
    data = FinancialData(
        current_assets=100.0, current_liabilities=50.0,
    )
    result = quick_ratio(data)
    assert result.status == "OK"
    assert result.value == pytest.approx(100.0 / 50.0)  # inventory = 0


def test_cash_ratio(full_data):
    result = cash_ratio(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(4_000_000_000.0 / 10_000_000_000.0)


def test_current_ratio_zero_liabilities():
    data = FinancialData(current_assets=100.0, current_liabilities=0.0)
    result = current_ratio(data)
    assert result.status == "NOT_MEANINGFUL"
    assert result.value is None


# ─── Leverage Tests ────────────────────────────────────────

def test_debt_to_equity(full_data):
    result = debt_to_equity(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(15_000_000_000.0 / 50_000_000_000.0)


def test_debt_to_equity_fallback_to_total_liabilities():
    data = FinancialData(
        total_liabilities=30_000_000.0, equity=50_000_000.0,
    )
    result = debt_to_equity(data)
    assert result.status == "OK"
    assert result.value == pytest.approx(30_000_000.0 / 50_000_000.0)
    assert any("total_liabilities" in w for w in result.warnings)


def test_debt_to_asset(full_data):
    result = debt_to_asset(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(15_000_000_000.0 / 80_000_000_000.0)


def test_interest_coverage(full_data):
    result = interest_coverage(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(8_000_000_000.0 / 1_000_000_000.0)


def test_interest_coverage_zero_interest():
    data = FinancialData(
        operating_income=8_000_000.0, interest_expense=0.0,
    )
    result = interest_coverage(data)
    assert result.status == "NOT_MEANINGFUL"
    assert result.value is None


# ─── Efficiency Tests ──────────────────────────────────────

def test_inventory_turnover(full_data):
    result = inventory_turnover(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(30_000_000_000.0 / 4_500_000_000.0)
    assert len(result.warnings) == 0  # میانگین موجود است


def test_inventory_turnover_without_avg():
    data = FinancialData(
        cost_of_goods_sold=30_000_000.0, inventory=5_000_000.0,
    )
    result = inventory_turnover(data)
    assert result.status == "OK"
    assert result.value == pytest.approx(30_000_000.0 / 5_000_000.0)
    assert any("میانگین" in w for w in result.warnings)


def test_fixed_asset_turnover(full_data):
    result = fixed_asset_turnover(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(50_000_000_000.0 / 38_000_000_000.0)


def test_receivables_collection_period(full_data):
    result = receivables_collection_period(full_data)
    assert result.status == "OK"
    ratio = 2_800_000_000.0 / 50_000_000_000.0
    expected_days = ratio * 365
    assert result.value == pytest.approx(expected_days)


# ─── Dividend Tests ────────────────────────────────────────

def test_dividend_payout_ratio(full_data):
    result = dividend_payout_ratio(full_data)
    assert result.status == "OK"
    assert result.value == pytest.approx(2000.0 / 6000.0)


def test_dividend_payout_ratio_negative_eps():
    data = FinancialData(
        dividend_per_share=500.0, eps=-200.0,
    )
    result = dividend_payout_ratio(data)
    assert result.status == "NOT_MEANINGFUL"
    assert result.value is None


def test_dividend_payout_ratio_zero_eps():
    data = FinancialData(
        dividend_per_share=500.0, eps=0.0,
    )
    result = dividend_payout_ratio(data)
    assert result.status == "NOT_MEANINGFUL"


# ─── Aggregate Tests ───────────────────────────────────────

def test_calculate_all_ratios_returns_all_19(full_data):
    results = calculate_all_ratios(full_data)
    assert len(results) == 19
    # همه باید OK باشند با داده‌ی کامل
    for key, result in results.items():
        assert isinstance(result, RatioResult)
        assert result.key == key
        assert result.status == "OK", f"{key} status is {result.status}"
        assert result.value is not None, f"{key} value is None"


def test_calculate_all_ratios_empty_data_returns_unavailable(empty_data):
    results = calculate_all_ratios(empty_data)
    assert len(results) == 19
    for key, result in results.items():
        assert result.status in ("UNAVAILABLE", "NOT_MEANINGFUL")
        assert result.value is None


def test_calculate_all_ratios_negative_eps():
    data = FinancialData(
        market_price=5000.0, eps=-200.0,
        net_income=-200_000_000.0, revenue=10_000_000_000.0,
    )
    results = calculate_all_ratios(data)
    assert results["pe"].status == "NOT_MEANINGFUL"
    assert results["peg"].status in ("NOT_MEANINGFUL", "UNAVAILABLE")
    assert results["payout_ratio"].status == "NOT_MEANINGFUL"


# ─── RatioResult Dataclass Tests ────────────────────────────

def test_ratio_result_as_dict():
    result = RatioResult(
        key="test", name="Test", category="test",
        value=1.5, formula="a/b", status="OK",
    )
    d = result.as_dict()
    assert d["key"] == "test"
    assert d["value"] == 1.5
    assert d["status"] == "OK"
    assert d["warnings"] == []


def test_ratio_result_is_immutable():
    result = RatioResult(
        key="test", name="Test", category="test",
        value=1.0, formula="a/b", status="OK",
    )
    with pytest.raises(Exception):
        result.value = 2.0
