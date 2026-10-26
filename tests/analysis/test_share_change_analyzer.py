"""Offline tests for ShareChangeAnalyzer — no network."""
from __future__ import annotations

from arya.analysis.analyzers.share_change_analyzer import ShareChangeAnalyzer
from arya.providers.shareholders.mock_provider import MockShareholderProvider


def test_missing_data_zero_score():
    p = MockShareholderProvider()
    m = p.fetch_shareholder_flow("UNKNOWN")
    s = ShareChangeAnalyzer().analyze(m)
    assert s.section == "smart_money"
    assert s.score == 0.0
    assert s.confidence == 0.0
    assert s.details["data_quality"] == "missing"


def test_accumulation_positive():
    p = MockShareholderProvider()
    m = p.fetch_shareholder_flow("ACCUM")
    s = ShareChangeAnalyzer().analyze(m)
    assert s.score > 0
    assert s.confidence > 0
    assert s.details["data_quality"] == "usable"


def test_distribution_negative():
    p = MockShareholderProvider()
    m = p.fetch_shareholder_flow("DIST")
    s = ShareChangeAnalyzer().analyze(m)
    assert s.score < 0
    assert s.confidence > 0
