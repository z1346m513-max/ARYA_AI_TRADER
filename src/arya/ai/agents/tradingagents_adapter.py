"""Optional, isolated bridge to TauricResearch/TradingAgents.

The upstream framework is loaded only when requested. Its categorical rating is
returned as separate research evidence and is never converted into ARYA's
quantitative score, recommendation, risk assessment, or order authorization.
"""
from __future__ import annotations

import copy
import importlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock
from types import ModuleType
from typing import Any


_SUPPORTED_ASSET_CLASSES = {
    "international_stock": "stock",
    "crypto": "crypto",
}
_SUPPORTED_ANALYSTS = {"market", "news", "fundamentals", "social"}
_SUPPORTED_RATINGS = {"Buy", "Overweight", "Hold", "Underweight", "Sell", "REVIEW"}
_RUN_LOCK = RLock()


class TradingAgentsIntegrationError(RuntimeError):
    """Base error for the optional TradingAgents integration."""


class TradingAgentsDependencyError(TradingAgentsIntegrationError):
    """Raised when the separately installed upstream package is unavailable."""


@dataclass(frozen=True)
class TradingAgentsOptions:
    """Non-secret runtime options for one TradingAgents research workflow."""

    selected_analysts: tuple[str, ...] = ("market", "news", "fundamentals", "social")
    output_language: str = "Persian"
    max_debate_rounds: int = 1
    max_risk_discuss_rounds: int = 1
    llm_provider: str | None = None
    quick_think_llm: str | None = None
    deep_think_llm: str | None = None
    data_dir: Path | None = None
    save_report: bool = True

    def __post_init__(self) -> None:
        analysts = tuple(self.selected_analysts)
        if not analysts:
            raise ValueError("At least one TradingAgents analyst must be selected.")
        unknown = sorted(set(analysts) - _SUPPORTED_ANALYSTS)
        if unknown:
            raise ValueError(f"Unsupported analyst(s): {', '.join(unknown)}")
        if len(set(analysts)) != len(analysts):
            raise ValueError("selected_analysts must not contain duplicates.")
        if not isinstance(self.output_language, str) or not self.output_language.strip():
            raise ValueError("output_language must not be empty.")
        for name, value in (
            ("max_debate_rounds", self.max_debate_rounds),
            ("max_risk_discuss_rounds", self.max_risk_discuss_rounds),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")
        object.__setattr__(self, "selected_analysts", analysts)
        if self.data_dir is not None:
            object.__setattr__(self, "data_dir", Path(self.data_dir).expanduser())


@dataclass(frozen=True)
class TradingAgentsResearchResult:
    """A separate external research result; not an ARYA trading recommendation."""

    ticker: str
    trade_date: str
    asset_class: str
    rating: str
    framework_version: str
    report_path: Path | None = None

    @property
    def requires_review(self) -> bool:
        """True when upstream could not extract a well-formed 5-tier rating."""
        return self.rating == "REVIEW"


class TradingAgentsAdapter:
    """Run upstream multi-agent research without changing ARYA's core path.

    Supported asset classes are explicitly named international_stock and crypto.
    ARYA's own stock market means Iran/TSETMC and must not be sent through this
    Yahoo/SEC-backed adapter.
    """

    def __init__(self, options: TradingAgentsOptions | None = None) -> None:
        self.options = options or TradingAgentsOptions()

    @staticmethod
    def _load_upstream() -> tuple[ModuleType, type, dict[str, Any]]:
        try:
            package = importlib.import_module("tradingagents")
            graph_module = importlib.import_module("tradingagents.graph.trading_graph")
            config_module = importlib.import_module("tradingagents.default_config")
        except (ImportError, ModuleNotFoundError) as exc:
            raise TradingAgentsDependencyError(
                "TradingAgents is an optional dependency. Use Python 3.11+ and run "
                "'python -m pip install -r requirements-tradingagents.txt'."
            ) from exc

        graph_class = getattr(graph_module, "TradingAgentsGraph", None)
        default_config = getattr(config_module, "DEFAULT_CONFIG", None)
        if graph_class is None or not isinstance(default_config, dict):
            raise TradingAgentsIntegrationError(
                "The installed TradingAgents package does not expose the expected "
                "v0.7.1 Python API (TradingAgentsGraph / DEFAULT_CONFIG)."
            )
        return package, graph_class, default_config

    def _build_config(self, default_config: dict[str, Any]) -> dict[str, Any]:
        config = copy.deepcopy(default_config)
        root = self.options.data_dir or (Path.home() / ".arya" / "tradingagents")
        root = root.expanduser()
        results_dir = root / "results"
        cache_dir = root / "cache"
        memory_path = root / "memory" / "trading_memory.md"

        # Keep third-party state outside the repository's tracked data directory.
        results_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        memory_path.parent.mkdir(parents=True, exist_ok=True)

        config.update(
            {
                "results_dir": str(results_dir),
                "data_cache_dir": str(cache_dir),
                "memory_log_path": str(memory_path),
                "checkpoint_enabled": False,
                "output_language": self.options.output_language,
                "max_debate_rounds": self.options.max_debate_rounds,
                "max_risk_discuss_rounds": self.options.max_risk_discuss_rounds,
            }
        )
        optional_overrides = {
            "llm_provider": self.options.llm_provider,
            "quick_think_llm": self.options.quick_think_llm,
            "deep_think_llm": self.options.deep_think_llm,
        }
        for key, value in optional_overrides.items():
            if value:
                config[key] = value
        return config

    @staticmethod
    def _validate_run(ticker: str, trade_date: str, asset_class: str) -> tuple[str, str]:
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("ticker must be a non-empty string.")
        normalized_ticker = ticker.strip()
        if asset_class not in _SUPPORTED_ASSET_CLASSES:
            supported = ", ".join(sorted(_SUPPORTED_ASSET_CLASSES))
            raise ValueError(
                f"asset_class must be one of: {supported}. "
                "Iran/TSETMC stocks and forex are not supported by this adapter."
            )
        try:
            parsed_date = datetime.strptime(trade_date, "%Y-%m-%d")
        except (TypeError, ValueError) as exc:
            raise ValueError("trade_date must use the exact YYYY-MM-DD format.") from exc
        if parsed_date.strftime("%Y-%m-%d") != trade_date:
            raise ValueError("trade_date must use the exact YYYY-MM-DD format.")
        return normalized_ticker, _SUPPORTED_ASSET_CLASSES[asset_class]

    @staticmethod
    def _build_portfolio(portfolio: Mapping[str, Any] | None) -> Any | None:
        if portfolio is None:
            return None
        if not isinstance(portfolio, Mapping):
            raise TypeError("portfolio must be a mapping or None.")
        try:
            portfolio_module = importlib.import_module("tradingagents.portfolio")
            portfolio_class = getattr(portfolio_module, "PortfolioContext")
            return portfolio_class.model_validate(dict(portfolio))
        except (ImportError, AttributeError, TypeError, ValueError) as exc:
            raise TradingAgentsIntegrationError(
                "The supplied portfolio could not be validated by TradingAgents."
            ) from exc

    def analyze(
        self,
        ticker: str,
        trade_date: str,
        *,
        asset_class: str,
        portfolio: Mapping[str, Any] | None = None,
    ) -> TradingAgentsResearchResult:
        """Run one research pass and return the upstream categorical rating.

        portfolio=None means holdings are unknown. Passing {"positions": []}
        explicitly tells the upstream framework the book is flat; these states
        must not be confused.
        """
        normalized_ticker, upstream_asset_type = self._validate_run(
            ticker, trade_date, asset_class
        )

        # Upstream currently maintains process-level configuration as well as a
        # per-run context. Serialize calls from this adapter to avoid cross-run
        # configuration races inside one ARYA process.
        with _RUN_LOCK:
            package, graph_class, default_config = self._load_upstream()
            config = self._build_config(default_config)
            portfolio_context = self._build_portfolio(portfolio)
            try:
                graph = graph_class(
                    selected_analysts=self.options.selected_analysts,
                    debug=False,
                    config=config,
                )
                final_state, rating = graph.propagate(
                    normalized_ticker,
                    trade_date,
                    asset_type=upstream_asset_type,
                    portfolio=portfolio_context,
                )
            except Exception as exc:
                raise TradingAgentsIntegrationError(
                    f"TradingAgents research run failed for {normalized_ticker} "
                    f"on {trade_date}: {type(exc).__name__}: {exc}"
                ) from exc

            rating = str(rating)
            if rating not in _SUPPORTED_RATINGS:
                raise TradingAgentsIntegrationError(
                    f"Unexpected TradingAgents rating {rating!r}; result was not accepted."
                )

            report_path: Path | None = None
            if self.options.save_report:
                try:
                    report_path = Path(graph.save_reports(final_state, normalized_ticker))
                except Exception as exc:
                    raise TradingAgentsIntegrationError(
                        f"TradingAgents analysis completed but report saving failed: {exc}"
                    ) from exc

        return TradingAgentsResearchResult(
            ticker=normalized_ticker,
            trade_date=trade_date,
            asset_class=asset_class,
            rating=rating,
            framework_version=str(getattr(package, "__version__", "unknown")),
            report_path=report_path,
        )
