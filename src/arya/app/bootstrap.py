"""
Bootstrap: نقطه‌ی مرکزی راه‌اندازی برنامه.
"""
from __future__ import annotations

import logging

from arya.analysis.analyzers.technical_analyzer import TechnicalAnalyzer
from arya.analysis.recommendation.recommendation_engine import RecommendationEngine
from arya.analysis.scoring.scoring_engine import ScoringEngine
from arya.ai.reasoning.decision_engine import RuleBasedDecisionEngine
from arya.config.settings import Settings
from arya.models.analysis_result import Recommendation
from arya.models.market_data import Symbol
from arya.providers.base import ProviderRegistry
import arya.providers.market.mock_provider  # noqa: F401
import arya.providers.market.tsetmc_provider  # noqa: F401
from arya.risk.risk_manager import RiskManager
from arya.storage.cache import OHLCVStore
from arya.storage.history_cache import SQLiteHistoryCache
from arya.storage.history_service import HistoryResult, MarketHistoryService
from arya.technical.indicator_engine import IndicatorEngine

logger = logging.getLogger(__name__)


class AryaApp:
    """Facade کلی برنامه - تمام لایه‌ها این‌جا Wire می‌شوند."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()
        self._configure_logging()

        self.store = OHLCVStore(self.settings.app["storage"]["path"])
        self.history_cache = SQLiteHistoryCache(self.settings.app["storage"]["path"])
        self._history_services: dict[str, MarketHistoryService] = {}

        self.indicator_engine = IndicatorEngine(self.settings)
        self.technical_analyzer = TechnicalAnalyzer()
        self.scoring_engine = ScoringEngine(self.settings)
        self.decision_engine = RuleBasedDecisionEngine()
        self.risk_manager = RiskManager()
        self.recommendation_engine = RecommendationEngine()

    def _configure_logging(self) -> None:
        level = getattr(
            logging,
            self.settings.app.get("logging", {}).get("level", "INFO"),
        )
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        )

    def _provider_for_market(self, market: str):
        cfg = self.settings.provider_for(market)
        driver = cfg.get("driver", "mock")
        kwargs = {"market": market}
        if driver == "tsetmc" and "adjust" in cfg:
            kwargs["adjust"] = cfg["adjust"]
        return ProviderRegistry.create(driver, **kwargs)

    def _history_service_for_market(self, market: str) -> MarketHistoryService:
        service = self._history_services.get(market)
        if service is None:
            service = MarketHistoryService(
                settings=self.settings,
                cache=self.history_cache,
                provider=self._provider_for_market(market),
            )
            self._history_services[market] = service
        return service

    def analyze_symbol(
        self,
        ticker: str,
        market: str = "stock",
        timeframe: str = "1d",
        *,
        analysis_settings: Settings | None = None,
    ) -> Recommendation:
        """اجرای کامل پایپ‌لاین با تنظیمات پایه یا override مستقل."""
        runtime_settings = analysis_settings or self.settings
        symbol = Symbol(ticker=ticker, market=market)
        runtime = runtime_settings.analysis.get("runtime", {})
        history_limit = int(runtime.get("history_limit", 200))

        # 1) Smart market-history cache -> provider refresh/fallback
        if runtime_settings is self.settings:
            history_service = self._history_service_for_market(market)
        else:
            history_service = MarketHistoryService(
                settings=runtime_settings,
                cache=self.history_cache,
                provider=self._provider_for_market(market),
            )
        history: HistoryResult = history_service.get_or_refresh(
            symbol,
            timeframe=timeframe,
            limit=history_limit,
            adjust=runtime_settings.provider_for(market).get("adjust", False),
        )
        if history.warning:
            logger.warning("%s", history.warning)

        # 2) Legacy OHLCV store remains the pipeline hand-off cache.
        self.store.save(history.series)
        df = history.series.to_dataframe()

        # 3) Indicator Engine
        indicator_results = IndicatorEngine(runtime_settings).run(df)

        # 4) Analysis Engine
        technical_section = self.technical_analyzer.analyze(indicator_results)
        section_scores = [technical_section]

        # 5) Scoring Engine
        overall_score, overall_confidence, section_scores = ScoringEngine(
            runtime_settings
        ).combine(section_scores)

        # 6) AI Decision Engine
        language = runtime_settings.app.get("app", {}).get("language", "fa")
        decision_cfg = runtime_settings.analysis.get("runtime", {}).get("decision", {})
        decision = RuleBasedDecisionEngine().decide(
            overall_score,
            overall_confidence,
            section_scores,
            language=language,
            buy_threshold=float(decision_cfg.get("buy_threshold", 0.25)),
            sell_threshold=float(decision_cfg.get("sell_threshold", -0.25)),
        )

        # 7) Risk Manager
        risk_cfg = runtime_settings.analysis.get("runtime", {}).get("risk", {})
        risk = RiskManager().assess(df, decision, config=risk_cfg)

        # 8) Recommendation Engine
        return self.recommendation_engine.build(
            symbol=str(symbol),
            df=df,
            decision=decision,
            risk=risk,
            section_scores=section_scores,
        )

    def refresh_market_history(
        self,
        market: str = "stock",
        limit: int = 200,
    ) -> list[HistoryResult]:
        """Scheduler entry point: refresh only cache entries that are due."""
        return self._history_service_for_market(market).refresh_cached_keys(
            market=market,
            limit=limit,
            adjust=self.settings.provider_for(market).get("adjust", False),
        )

    def list_symbols(self, market: str = "stock") -> list[Symbol]:
        return self._provider_for_market(market).list_symbols()
