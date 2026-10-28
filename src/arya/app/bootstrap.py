"""
Bootstrap: نقطه‌ی مرکزی راه‌اندازی برنامه. تمام لایه‌های پایپ‌لاین را می‌سازد
و متد analyze_symbol() را در اختیار CLI / Dashboard / Scheduler قرار می‌دهد.

زنجیره‌ی اجرا دقیقاً منطبق بر دیاگرام معماری است:

    Providers -> Storage -> Indicator Engine -> Analysis Engine ->
    Scoring Engine -> AI Decision Engine -> Risk Manager ->
    Recommendation Engine -> Dashboard
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from arya.analysis.analyzers.technical_analyzer import TechnicalAnalyzer
from arya.analysis.analyzers.fundamental_analyzer import FundamentalAnalyzer
from arya.analysis.recommendation.recommendation_engine import RecommendationEngine
from arya.analysis.scoring.scoring_engine import ScoringEngine
from arya.ai.reasoning.decision_engine import RuleBasedDecisionEngine
from arya.config.settings import Settings
from arya.models.analysis_result import Recommendation
from arya.models.fundamentals import FundamentalMetrics
from arya.models.market_data import Symbol
from arya.data_quality import OHLCVQualityError, snapshot_sha256, validate_ohlcv_series
from arya.providers.base import ProviderRegistry
import arya.providers.market.mock_provider  # noqa: F401  (ثبت درایور "mock")
import arya.providers.market.tsetmc_provider  # noqa: F401  (ثبت درایور "tsetmc")
from arya.risk.risk_manager import RiskManager
from arya.storage.cache import OHLCVStore
from arya.technical.indicator_engine import IndicatorEngine
from arya.scanner.filters import MarketFilterConfig, FilterResult, scan_ohlcv
from arya.technical.strategies.trend_momentum import StrategySignal, trend_momentum_signal

logger = logging.getLogger(__name__)


class AryaApp:
    """Facade کلی برنامه - تمام لایه‌ها این‌جا Wire می‌شوند."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()
        self._configure_logging()

        self.store = OHLCVStore(self.settings.app["storage"]["path"])
        self.indicator_engine = IndicatorEngine(self.settings)
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.scoring_engine = ScoringEngine(self.settings)
        self.decision_engine = RuleBasedDecisionEngine()
        self.risk_manager = RiskManager()
        self.recommendation_engine = RecommendationEngine()

    def _configure_logging(self) -> None:
        level = getattr(logging, self.settings.app.get("logging", {}).get("level", "INFO"))
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        )

    def _provider_for_market(self, market: str):
        cfg = self.settings.provider_for(market)
        driver = cfg.get("driver", "mock")
        kwargs = {"market": market}
        if driver == "tsetmc":
            for key in ("base_url", "timeout_seconds", "retries", "backoff_seconds"):
                if key in cfg:
                    kwargs[{"timeout_seconds": "timeout"}.get(key, key)] = cfg[key]
        return ProviderRegistry.create(driver, **kwargs)

    def _fetch_validated_series(self, ticker: str, market: str, timeframe: str, limit: int = 200):
        """Fetch, validate, and persist provenance before data reaches analysis."""
        provider = self._provider_for_market(market)
        series = provider.fetch_ohlcv(Symbol(ticker=ticker, market=market), timeframe=timeframe, limit=limit)
        retrieved_at = datetime.now(timezone.utc).isoformat()
        report = validate_ohlcv_series(series)
        run_id = uuid.uuid4().hex
        self.store.record_data_quality(
            run_id=run_id,
            series=series,
            provider=provider.name,
            retrieved_at_utc=retrieved_at,
            report=report,
            data_hash=snapshot_sha256(series),
        )
        if not report.is_valid:
            raise OHLCVQualityError(report)
        return series, run_id

    def analyze_symbol(self, ticker: str, market: str = "stock", timeframe: str = "1d") -> Recommendation:
        """اجرای کامل پایپ‌لاین برای یک نماد و برگرداندن Recommendation نهایی."""
        symbol = Symbol(ticker=ticker, market=market)

        # 1) Providers + fail-closed data-quality/provenance gate
        series, data_quality_run_id = self._fetch_validated_series(ticker, market, timeframe)

        # 2) Storage (کش کردن برای فراخوانی‌های بعدی)
        self.store.save(series)

        df = series.to_dataframe()

        # 3) Indicator Engine
        indicator_results = self.indicator_engine.run(df)

        # 4) Analysis Engine (فعلا فقط بخش technical پیاده‌سازی شده)
        technical_section = self.technical_analyzer.analyze(indicator_results)
        section_scores = [technical_section]

        # 5) Scoring Engine
        overall_score, overall_confidence, section_scores = self.scoring_engine.combine(section_scores)

        # 6) AI Decision Engine
        decision = self.decision_engine.decide(overall_score, overall_confidence, section_scores)

        # 7) Risk Manager
        risk = self.risk_manager.assess(df, decision)

        # 8) Recommendation Engine
        recommendation = self.recommendation_engine.build(
            symbol=str(symbol),
            df=df,
            decision=decision,
            risk=risk,
            section_scores=section_scores,
            data_quality_run_id=data_quality_run_id,
        )

        return recommendation

    def list_symbols(self, market: str = "stock") -> list[Symbol]:
        return self._provider_for_market(market).list_symbols()

    def evaluate_market_filter(self, ticker: str, market: str = "stock", timeframe: str = "1d") -> FilterResult:
        """فیلتر کمّی آخرین وضعیت نماد را بدون تولید توصیهٔ معاملاتی برمی‌گرداند."""
        series, _ = self._fetch_validated_series(ticker, market, timeframe)
        cfg = MarketFilterConfig(**self.settings.filters.get("market_watch", {}))
        return scan_ohlcv(series.to_dataframe(), cfg)

    def evaluate_strategy(self, ticker: str, market: str = "stock", timeframe: str = "1d") -> StrategySignal:
        """استراتژی قابل توضیح را روی دادهٔ آخر provider اجرا می‌کند."""
        series, _ = self._fetch_validated_series(ticker, market, timeframe)
        cfg = self.settings.filters.get("strategy", {})
        cfg = {k: v for k, v in cfg.items() if k != "name"}
        return trend_momentum_signal(series.to_dataframe(), **cfg)

    def analyze_fundamentals(self, metrics: FundamentalMetrics):
        """تحلیل نسبت‌های بنیادی تزریق‌شده از Codal یا منبع معتبر دیگر."""
        return self.fundamental_analyzer.analyze(metrics)
