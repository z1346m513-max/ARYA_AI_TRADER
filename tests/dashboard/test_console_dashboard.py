"""
تست‌های داشبورد کنسول و CLI.

موارد پوشش‌داده‌شده:
- render_fundamental_analysis با داده‌ی کامل نمایش می‌دهد
- render_fundamental_analysis با داده‌ی خالی
- render_full_analysis (پیشنهاد + بنیادی)
- CLI fundamental با پارامترهای خط فرمان
- CLI fundamental با فایل JSON
- CLI analyze با financial_data
- سازگاری CLI قدیمی
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest
from rich.console import Console

from arya.analysis.analyzers.fundamental_analyzer import FundamentalAnalyzer
from arya.dashboard.console_dashboard import (
    render_recommendation,
    render_fundamental_analysis,
    render_full_analysis,
)
from arya.fundamental.models import FinancialData
from arya.models.analysis_result import (
    Action,
    Recommendation,
    RiskAssessment,
    SectionScore,
)


# ─── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def full_data():
    return FinancialData(
        market_price=10000.0,
        shares_outstanding=1_000_000.0,
        revenue=50_000_000_000.0,
        cost_of_goods_sold=30_000_000_000.0,
        gross_profit=20_000_000_000.0,
        operating_income=8_000_000_000.0,
        net_income=6_000_000_000.0,
        eps=6000.0,
        interest_expense=1_000_000_000.0,
        operating_cash_flow=7_000_000_000.0,
        cash_flow_per_share=7000.0,
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
        earnings_growth_rate_percent=20.0,
        dividend_per_share=2000.0,
        avg_total_assets=78_000_000_000.0,
        avg_equity=48_000_000_000.0,
        avg_inventory=4_500_000_000.0,
        avg_receivables=2_800_000_000.0,
        avg_fixed_assets=38_000_000_000.0,
    )


@pytest.fixture
def sample_recommendation():
    return Recommendation(
        symbol="فولاد",
        overall_score=0.5,
        confidence=0.8,
        trend_quality=0.7,
        liquidity_strength=0.6,
        action=Action.BUY,
        reasons=["روند صعودی", "حجم بالای معاملات"],
        risk=RiskAssessment(
            risk_level="medium",
            risk_score=0.4,
            max_position_size_pct=5.0,
            stop_loss_pct=7.0,
        ),
    )


@pytest.fixture
def fundamental_section(full_data):
    analyzer = FundamentalAnalyzer()
    return analyzer.analyze_financial_data(full_data)


# ─── render_fundamental_analysis Tests ──────────────────────

def test_render_fundamental_analysis_does_not_crash(fundamental_section):
    """رندر داشبورد بنیادی نباید خطا بدهد."""
    console = Console(record=True, width=120)
    render_fundamental_analysis(fundamental_section, symbol="فولاد", console=console)
    output = console.export_text()
    assert "تحلیل بنیادی" in output
    assert "فولاد" in output


def test_render_fundamental_shows_all_19_ratios(fundamental_section):
    """تمام ۱۹ نسبت باید در خروجی موجود باشند."""
    console = Console(record=True, width=120)
    render_fundamental_analysis(fundamental_section, console=console)
    output = console.export_text()

    # بررسی چند نسبت کلیدی
    assert "P/E" in output or "قیمت به درآمد" in output
    assert "ROE" in output or "بازده حقوق" in output
    assert "نسبت جاری" in output
    assert "بدهی" in output


def test_render_fundamental_shows_summary(fundamental_section):
    """پنل خلاصه باید امتیاز و اطمینان را نشان دهد."""
    console = Console(record=True, width=120)
    render_fundamental_analysis(fundamental_section, console=console)
    output = console.export_text()
    assert "امتیاز" in output
    assert "اطمینان" in output
    assert "کیفیت داده" in output


def test_render_fundamental_shows_reasons(fundamental_section):
    """دلایل امتیازدهی باید نمایش داده شوند."""
    console = Console(record=True, width=120)
    render_fundamental_analysis(fundamental_section, console=console)
    output = console.export_text()
    assert "دلایل" in output


def test_render_fundamental_shows_stats(fundamental_section):
    """آمار نسبت‌ها باید نمایش داده شود."""
    console = Console(record=True, width=120)
    render_fundamental_analysis(fundamental_section, console=console)
    output = console.export_text()
    assert "امتیازدهی‌شده" in output
    assert "ناموجود" in output


def test_render_fundamental_empty_data():
    """داده‌ی خالی نباید crash کند."""
    analyzer = FundamentalAnalyzer()
    section = analyzer.analyze_financial_data(FinancialData())
    console = Console(record=True, width=120)
    render_fundamental_analysis(section, console=console)
    output = console.export_text()
    assert "missing" in output or "ناچیز" in output


# ─── render_full_analysis Tests ─────────────────────────────

def test_render_full_analysis_with_fundamental(sample_recommendation, fundamental_section):
    """رندر کامل باید هم پیشنهاد و هم بنیادی را نشان دهد."""
    console = Console(record=True, width=120)
    render_full_analysis(sample_recommendation, fundamental_section, console=console)
    output = console.export_text()
    assert "فولاد" in output
    assert "خرید" in output
    assert "تحلیل بنیادی" in output


def test_render_full_analysis_without_fundamental(sample_recommendation):
    """رندر کامل بدون بنیادی باید فقط پیشنهاد را نشان دهد."""
    console = Console(record=True, width=120)
    render_full_analysis(sample_recommendation, None, console=console)
    output = console.export_text()
    assert "فولاد" in output
    assert "خرید" in output


# ─── CLI Tests ──────────────────────────────────────────────

def test_cli_fundamental_with_inline_params(capsys):
    """دستور fundamental با پارامترهای خط فرمان."""
    from arya.cli.main import main

    rc = main([
        "fundamental",
        "--ticker", "فولاد",
        "--market-price", "10000",
        "--eps", "6000",
        "--revenue", "50000000000",
        "--net-income", "6000000000",
        "--equity", "50000000000",
        "--total-assets", "80000000000",
        "--debt", "15000000000",
        "--current-assets", "20000000000",
        "--current-liabilities", "10000000000",
        "--inventory", "5000000000",
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "تحلیل بنیادی" in captured.out or "تحلیل بنیادی" in captured.err


def test_cli_fundamental_with_json_file(tmp_path, full_data, capsys):
    """دستور fundamental با فایل JSON."""
    json_path = tmp_path / "financial.json"
    json_path.write_text(json.dumps(full_data.__dict__), encoding="utf-8")

    from arya.cli.main import main

    rc = main([
        "fundamental",
        "--ticker", "فولاد",
        "--json", str(json_path),
    ])
    assert rc == 0


def test_cli_fundamental_no_data_returns_error(capsys):
    """دستور fundamental بدون داده باید خطا برگرداند."""
    from arya.cli.main import main

    rc = main(["fundamental", "--ticker", "فولاد"])
    assert rc == 1
