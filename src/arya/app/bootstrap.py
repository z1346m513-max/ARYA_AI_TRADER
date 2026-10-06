"""
Bootstrap: پایپ‌لاین ARYA — بورس ایران + کدال + Cache-First.
"""
from __future__ import annotations

import logging

from arya.analysis.analyzers.codal_event_analyzer import CodalEventAnalyzer
from arya.analysis.analyzers.fundamental_analyzer import FundamentalAnalyzer
from arya.analysis.analyzers.technical_analyzer import TechnicalAnalyzer
from arya.analysis.recommendation.recommendation_engine import RecommendationEngine
from arya.analysis.scoring.scoring_engine import ScoringEngine
from arya.ai.reasoning.decision_engine import RuleBasedDecisionEngine
from arya.config.settings import Settings
from arya.models.analysis_result import Recommendation
from arya.models.fundamentals import FundamentalMetrics
from arya.models.market_data import Symbol
from arya.providers.base import ProviderRegistry
import arya.providers.market.mock_provider  # noqa: F401
import arya.providers.market.tsetmc_provider  # noqa: F401
from arya.providers.codal import CodalProvider, CodalProviderError
from arya.providers.codal.symbol_map import to_codal_symbol
from arya.risk.risk_manager import RiskManager
from arya.storage.cache import OHLCVStore
from arya.storage.cache_metrics import cache_metrics
from arya.technical.indicator_engine import IndicatorEngine
from arya.scanner.filters import MarketFilterConfig, FilterResult, scan_ohlcv
from arya.technical.strategies.trend_momentum import StrategySignal, trend_momentum_signal

logger = logging.getLogger(__name__)

ALLOWED_MARKETS = frozenset({"stock"})


class AryaApp:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()
        self._configure_logging()

        self.store = OHLCVStore(self.settings.app["storage"]["path"])
        self.indicator_engine = IndicatorEngine(self.settings)
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.codal_event_analyzer = CodalEventAnalyzer()
        self.scoring_engine = ScoringEngine(self.settings)
        self.decision_engine = RuleBasedDecisionEngine()
        self.risk_manager = RiskManager()
        self.recommendation_engine = RecommendationEngine()
        self._codal: CodalProvider | None = None

    def _configure_logging(self) -> None:
        level = getattr(logging, self.settings.app.get("logging", {}).get("level", "INFO"))
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        )

    def _assert_market(self, market: str) -> str:
        if market not in ALLOWED_MARKETS:
            raise ValueError(
                f"ARYA فقط بازار stock (بورس ایران) را پشتیبانی می‌کند؛ دریافت شد: {market!r}"
            )
        return market

    def _cache_ttl(self, timeframe: str) -> int:
        cache_cfg = self.settings.app.get("storage", {}).get("cache", {})
        if not cache_cfg.get("enabled", True):
            return 0
        ttl_map = cache_cfg.get("ttl_seconds", {})
        return int(ttl_map.get(timeframe, cache_cfg.get("default_ttl_seconds", 3600)))

    def _provider_for_market(self, market: str):
        market = self._assert_market(market)
        cfg = self.settings.provider_for(market)
        driver = cfg.get("driver", "mock")
        kwargs: dict = {"market": market}
        if driver == "tsetmc":
            for key in ("base_url", "timeout_seconds", "retries", "backoff_seconds"):
                if key in cfg:
                    kwargs[{"timeout_seconds": "timeout"}.get(key, key)] = cfg[key]
        return ProviderRegistry.create(driver, **kwargs)

    def _codal_provider(self) -> CodalProvider | None:
        codal_cfg = self.settings.providers.get("codal", {})
        if not codal_cfg.get("enabled", False):
            return None
        if self._codal is None:
            kwargs = {}
            if codal_cfg.get("base_url"):
                kwargs["base_url"] = codal_cfg["base_url"]
            if "timeout_seconds" in codal_cfg:
                kwargs["timeout"] = codal_cfg["timeout_seconds"]
            if "retries" in codal_cfg:
                kwargs["retries"] = codal_cfg["retries"]
            if "backoff_seconds" in codal_cfg:
                kwargs["backoff_seconds"] = codal_cfg["backoff_seconds"]
            if "min_interval_seconds" in codal_cfg:
                kwargs["min_interval_seconds"] = codal_cfg["min_interval_seconds"]
            self._codal = CodalProvider(**kwargs)
        return self._codal

    def _codal_section(self, ticker: str):
        provider = self._codal_provider()
        if provider is None:
            return None
        symbol = to_codal_symbol(ticker)
        try:
            letters = provider.fetch_recent(symbol, limit=10)
            return self.codal_event_analyzer.analyze(letters)
        except CodalProviderError as exc:
            logger.warning("کدال در دسترس نیست (%s): %s", symbol, exc)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("خطای غیرمنتظره کدال: %s", exc)
            return None

    def _fetch_series(
        self,
        symbol: Symbol,
        timeframe: str,
        *,
        limit: int = 200,
        force_refresh: bool = False,
    ):
        ttl = self._cache_ttl(timeframe)
        cache_cfg = self.settings.app.get("storage", {}).get("cache", {})
        enforce_min = bool(cache_cfg.get("enforce_min_candles", True))

        if force_refresh:
            cache_metrics.record_force_refresh()
            logger.info("cache BYPASS force_refresh %s", symbol)
        elif ttl > 0:
            lookup = self.store.get(
                symbol,
                timeframe,
                ttl_seconds=ttl,
                min_candles=limit if enforce_min else None,
            )
            if lookup.fresh and lookup.series is not None:
                logger.info(
                    "cache HIT fresh %s candles=%d",
                    symbol,
                    len(lookup.series.candles),
                )
                return lookup.series, "cache"
            logger.info(
                "cache %s %s reason=%s",
                "HIT" if lookup.hit else "MISS",
                symbol,
                lookup.reason,
            )

        provider = self._provider_for_market(symbol.market)
        series = provider.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        self.store.save(series)
        return series, "provider"

    def analyze_symbol(
        self,
        ticker: str,
        market: str = "stock",
        timeframe: str = "1d",
        *,
        force_refresh: bool = False,
        limit: int = 200,
    ) -> Recommendation:
        market = self._assert_market(market)
        symbol = Symbol(ticker=ticker, market=market)

        series, source = self._fetch_series(
            symbol, timeframe, limit=limit, force_refresh=force_refresh
        )
        logger.debug("OHLCV source=%s for %s", source, symbol)

        df = series.to_dataframe()
        indicator_results = self.indicator_engine.run(df)
        technical_section = self.technical_analyzer.analyze(indicator_results)
        section_scores = [technical_section]

        codal_section = self._codal_section(ticker)
        if codal_section is not None:
            section_scores.append(codal_section)

        overall_score, overall_confidence, section_scores = self.scoring_engine.combine(
            section_scores
        )
        decision = self.decision_engine.decide(overall_score, overall_confidence, section_scores)
        risk = self.risk_manager.assess(df, decision)
        recommendation = self.recommendation_engine.build(
            symbol=str(symbol),
            df=df,
            decision=decision,
            risk=risk,
            section_scores=section_scores,
        )

        if codal_section and codal_section.details.get("reasons"):
            existing = set(recommendation.reasons)
            for r in codal_section.details["reasons"]:
                if r not in existing:
                    recommendation.reasons.append(r)

        return recommendation

    def list_symbols(self, market: str = "stock") -> list[Symbol]:
        return self._provider_for_market(market).list_symbols()

    def evaluate_market_filter(self, ticker: str, market: str = "stock", timeframe: str = "1d") -> FilterResult:
        market = self._assert_market(market)
        series, _ = self._fetch_series(Symbol(ticker=ticker, market=market), timeframe)
        cfg = MarketFilterConfig(**self.settings.filters.get("market_watch", {}))
        return scan_ohlcv(series.to_dataframe(), cfg)

    def evaluate_strategy(self, ticker: str, market: str = "stock", timeframe: str = "1d") -> StrategySignal:
        market = self._assert_market(market)
        series, _ = self._fetch_series(Symbol(ticker=ticker, market=market), timeframe)
        cfg = self.settings.filters.get("strategy", {})
        cfg = {k: v for k, v in cfg.items() if k != "name"}
        return trend_momentum_signal(series.to_dataframe(), **cfg)

    def analyze_fundamentals(self, metrics: FundamentalMetrics):
        return self.fundamental_analyzer.analyze(metrics)

    def fetch_codal_letters(self, ticker: str, limit: int = 10):
        provider = self._codal_provider()
        if provider is None:
            raise CodalProviderError("کدال در providers.yaml غیرفعال است")
        return provider.fetch_recent(to_codal_symbol(ticker), limit=limit)

    def cache_stats(self):
        return cache_metrics.snapshot()
