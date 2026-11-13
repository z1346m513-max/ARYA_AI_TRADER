from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest

from arya.ai.agents import (
    TradingAgentsAdapter,
    TradingAgentsDependencyError,
    TradingAgentsOptions,
)


def install_fake_tradingagents(monkeypatch, tmp_path, rating="Buy"):
    root = ModuleType("tradingagents")
    root.__version__ = "0.7.1"

    graph_package = ModuleType("tradingagents.graph")
    graph_package.__path__ = []
    graph_module = ModuleType("tradingagents.graph.trading_graph")
    config_module = ModuleType("tradingagents.default_config")
    config_module.DEFAULT_CONFIG = {
        "llm_provider": "openai",
        "output_language": "English",
        "results_dir": "upstream-results",
        "data_cache_dir": "upstream-cache",
        "memory_log_path": "upstream-memory.md",
        "checkpoint_enabled": True,
        "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1,
    }

    portfolio_module = ModuleType("tradingagents.portfolio")

    class FakePortfolioContext:
        @classmethod
        def model_validate(cls, payload):
            return {"validated_portfolio": payload}

    portfolio_module.PortfolioContext = FakePortfolioContext

    class FakeTradingAgentsGraph:
        last_instance = None

        def __init__(self, selected_analysts, debug, config):
            self.selected_analysts = selected_analysts
            self.debug = debug
            self.config = config
            self.propagate_args = None
            FakeTradingAgentsGraph.last_instance = self

        def propagate(self, ticker, trade_date, asset_type="stock", portfolio=None):
            self.propagate_args = (ticker, trade_date, asset_type, portfolio)
            return {"final_trade_decision": "Rating: " + rating}, rating

        def save_reports(self, final_state, ticker):
            return Path(self.config["results_dir"]) / "reports" / ticker

    graph_module.TradingAgentsGraph = FakeTradingAgentsGraph

    monkeypatch.setitem(sys.modules, "tradingagents", root)
    monkeypatch.setitem(sys.modules, "tradingagents.graph", graph_package)
    monkeypatch.setitem(sys.modules, "tradingagents.graph.trading_graph", graph_module)
    monkeypatch.setitem(sys.modules, "tradingagents.default_config", config_module)
    monkeypatch.setitem(sys.modules, "tradingagents.portfolio", portfolio_module)
    return FakeTradingAgentsGraph, config_module.DEFAULT_CONFIG


def test_missing_optional_dependency_has_install_guidance(monkeypatch):
    original_import_module = importlib.import_module

    def fail_upstream(name, package=None):
        if name == "tradingagents":
            raise ModuleNotFoundError("No module named 'tradingagents'", name="tradingagents")
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fail_upstream)
    adapter = TradingAgentsAdapter(TradingAgentsOptions(save_report=False))
    with pytest.raises(TradingAgentsDependencyError, match="requirements-tradingagents.txt"):
        adapter.analyze("AAPL", "2026-11-13", asset_class="international_stock")


def test_iran_stock_and_forex_are_rejected_before_import(monkeypatch):
    def unexpected_import(*args, **kwargs):
        raise AssertionError("upstream must not be imported for unsupported markets")

    monkeypatch.setattr(importlib, "import_module", unexpected_import)
    adapter = TradingAgentsAdapter(TradingAgentsOptions(save_report=False))
    with pytest.raises(ValueError, match="Iran/TSETMC"):
        adapter.analyze("فولاد", "2026-11-13", asset_class="iran_stock")
    with pytest.raises(ValueError, match="Iran/TSETMC"):
        adapter.analyze("EURUSD", "2026-11-13", asset_class="forex")


def test_analyze_uses_isolated_config_and_keeps_rating_separate(monkeypatch, tmp_path):
    fake_graph, default_config = install_fake_tradingagents(monkeypatch, tmp_path)
    data_dir = tmp_path / "agent-data"
    options = TradingAgentsOptions(
        selected_analysts=("market", "news"),
        output_language="Persian",
        max_debate_rounds=2,
        llm_provider="ollama",
        data_dir=data_dir,
        save_report=True,
    )

    result = TradingAgentsAdapter(options).analyze(
        "AAPL",
        "2026-11-13",
        asset_class="international_stock",
    )

    instance = fake_graph.last_instance
    assert result.rating == "Buy"
    assert result.requires_review is False
    assert result.framework_version == "0.7.1"
    assert result.report_path == data_dir / "results" / "reports" / "AAPL"
    assert instance.propagate_args == ("AAPL", "2026-11-13", "stock", None)
    assert instance.selected_analysts == ("market", "news")
    assert instance.debug is False
    assert instance.config["llm_provider"] == "ollama"
    assert instance.config["output_language"] == "Persian"
    assert instance.config["max_debate_rounds"] == 2
    assert instance.config["checkpoint_enabled"] is False
    assert Path(instance.config["data_cache_dir"]).is_relative_to(data_dir)
    assert Path(instance.config["memory_log_path"]).is_relative_to(data_dir)
    assert default_config["checkpoint_enabled"] is True


def test_review_signal_is_not_silently_mapped_to_hold(monkeypatch, tmp_path):
    install_fake_tradingagents(monkeypatch, tmp_path, rating="REVIEW")
    result = TradingAgentsAdapter(
        TradingAgentsOptions(data_dir=tmp_path / "data", save_report=False)
    ).analyze("BTC-USD", "2026-11-13", asset_class="crypto")

    assert result.rating == "REVIEW"
    assert result.requires_review is True
    assert result.report_path is None


def test_explicit_portfolio_is_validated_and_forwarded(monkeypatch, tmp_path):
    fake_graph, _ = install_fake_tradingagents(monkeypatch, tmp_path)
    portfolio = {"cash": 1000.0, "currency": "USD", "positions": []}
    result = TradingAgentsAdapter(
        TradingAgentsOptions(data_dir=tmp_path / "data", save_report=False)
    ).analyze(
        "AAPL",
        "2026-11-13",
        asset_class="international_stock",
        portfolio=portfolio,
    )

    forwarded = fake_graph.last_instance.propagate_args[3]
    assert forwarded == {"validated_portfolio": portfolio}
    assert result.rating == "Buy"


@pytest.mark.parametrize("trade_date", ["2026-1-3", "13-11-2026", "not-a-date"])
def test_trade_date_must_be_canonical_iso(trade_date):
    adapter = TradingAgentsAdapter(TradingAgentsOptions(save_report=False))
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        adapter.analyze("AAPL", trade_date, asset_class="international_stock")


def test_options_reject_unknown_or_duplicate_analysts():
    with pytest.raises(ValueError, match="Unsupported analyst"):
        TradingAgentsOptions(selected_analysts=("market", "made_up"))
    with pytest.raises(ValueError, match="duplicates"):
        TradingAgentsOptions(selected_analysts=("market", "market"))
