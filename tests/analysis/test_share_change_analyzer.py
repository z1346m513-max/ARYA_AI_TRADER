"""Offline tests for ShareChangeAnalyzer — no network."""
from __future__ import annotations

from arya.analysis.analyzers.share_change_analyzer import ShareChangeAnalyzer
from arya.models.shareholders import ShareholderFlowMetrics
from arya.providers.shareholders.mock_provider import MockShareholderProvider


def test_missing_data_zero_score_and_confidence():
    metrics = MockShareholderProvider().fetch_shareholder_flow("UNKNOWN")
    score = ShareChangeAnalyzer().analyze(metrics)
    assert score.section == "smart_money"
    assert score.score == 0.0
    assert score.confidence == 0.0
    assert score.details["data_quality"] == "missing"


def test_accumulation_positive():
    metrics = MockShareholderProvider().fetch_shareholder_flow("ACCUM")
    score = ShareChangeAnalyzer().analyze(metrics)
    assert score.score > 0
    assert score.confidence > 0
    assert score.details["data_quality"] == "usable"


def test_distribution_negative():
    metrics = MockShareholderProvider().fetch_shareholder_flow("DIST")
    score = ShareChangeAnalyzer().analyze(metrics)
    assert score.score < 0
    assert score.confidence > 0


def test_partial_data_only_scores_signal_with_complete_inputs():
    metrics = ShareholderFlowMetrics(
        ticker="PARTIAL",
        individual_avg_buy_volume=200.0,
        individual_avg_sell_volume=100.0,
        data_quality="partial",
    )
    score = ShareChangeAnalyzer().analyze(metrics)
    assert score.score == 1.0
    assert score.confidence == 0.25
    assert score.details["signal_count"] == 1
    assert score.details["data_quality"] == "partial"


def test_partial_data_without_complete_signal_inputs_has_zero_confidence():
    metrics = ShareholderFlowMetrics(
        ticker="INCOMPLETE",
        legal_buy_volume_share=0.5,
        data_quality="partial",
    )
    score = ShareChangeAnalyzer().analyze(metrics)
    assert score.score == 0.0
    assert score.confidence == 0.0


def test_volume_fields_are_not_monetary_value_fields():
    metrics = ShareholderFlowMetrics(
        ticker="VOLUME",
        legal_net_buy_volume=1000.0,
        data_quality="partial",
    )
    payload = metrics.as_dict()
    assert payload["legal_net_buy_volume"] == 1000.0
    assert payload["legal_net_buy_value_rial"] is None
    assert "legal_net_buy_value" not in payload


def test_zero_denominator_does_not_create_average_or_share():
    provider = MockShareholderProvider()
    metrics = ShareholderFlowMetrics(
        ticker="ZERO",
        individual_avg_buy_volume=None,
        individual_avg_sell_volume=None,
        legal_buy_volume=0.0,
        legal_sell_volume=0.0,
        legal_net_buy_volume=0.0,
        legal_buy_volume_share=None,
        data_quality="partial",
    )
    score = ShareChangeAnalyzer().analyze(metrics)
    assert score.confidence == 0.0
    assert metrics.legal_buy_volume_share is None
