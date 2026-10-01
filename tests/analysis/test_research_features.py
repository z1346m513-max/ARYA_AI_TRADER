from datetime import datetime, timedelta, timezone

import pandas as pd

from arya.analysis.analyzers.fundamental_analyzer import FundamentalAnalyzer
from arya.models.fundamentals import FundamentalMetrics
from arya.scanner.filters import MarketFilterConfig, evaluate_market_filter, scan_ohlcv
from arya.technical.strategies.trend_momentum import trend_momentum_signal


def test_market_filter_detects_volume_confirmation_and_positive_close():
    result = evaluate_market_filter(
        {"close": 110, "previous_close": 100, "volume": 300, "average_volume": 100, "value": 10_000},
        MarketFilterConfig(min_price_change_pct=0, max_price_change_pct=15, min_volume_ratio=2, min_value=5_000, require_positive_close=True),
    )
    assert result.passed
    assert result.metrics["volume_ratio"] == 3


def test_market_filter_rejects_missing_buyer_power_when_requested():
    result = evaluate_market_filter(
        {"close": 100, "previous_close": 100, "volume": 200, "average_volume": 100},
        MarketFilterConfig(min_buyer_power=2),
    )
    assert not result.passed
    assert "buyer_power_not_confirmed" in result.reasons


def test_scan_ohlcv_uses_only_previous_candles_for_average_volume():
    df = pd.DataFrame({"close": [100, 101, 102, 104], "volume": [100, 100, 100, 300]})
    result = scan_ohlcv(df, MarketFilterConfig(min_volume_ratio=2, min_price_change_pct=-5, max_price_change_pct=5))
    assert result.passed


def test_trend_momentum_returns_explainable_signal():
    prices = [100 + i * 0.8 for i in range(70)]
    df = pd.DataFrame({"close": prices, "volume": [100] * len(prices)})
    signal = trend_momentum_signal(df)
    assert signal.action in {"buy", "hold", "sell"}
    assert signal.reasons
    assert -1 <= signal.score <= 1


def test_fundamental_ratios_and_missing_data_are_safe():
    metrics = FundamentalMetrics(
        eps=10, market_price=100, book_value_per_share=50,
        dividend_per_share=5, revenue=1_000, net_income=100,
        debt=500, equity=500, current_assets=300, current_liabilities=200,
    )
    assert metrics.pe == 10
    assert metrics.pb == 2
    assert metrics.dividend_yield == 0.05
    result = FundamentalAnalyzer().analyze(metrics)
    assert result.confidence > 0
    assert result.details["data_quality"] == "usable"
    assert FundamentalAnalyzer().analyze(FundamentalMetrics()).confidence == 0
