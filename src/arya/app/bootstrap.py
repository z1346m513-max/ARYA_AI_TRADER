"""
Bootstrap: نقطه‌ی مرکزی راه‌اندازی برنامه. تمام لایه‌های پایپ‌لاین را می‌سازد
و متد analyze_symbol() را در اختیار CLI / Dashboard / Scheduler قرار می‌دهد.

زنجیره‌ی اجرا:
    Providers -> Storage -> Indicator Engine -> Analysis Engine ->
    Scoring Engine -> AI Decision Engine -> Risk Manager ->
    Recommendation Engine -> Dashboard
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
import arya.providers.market.mock_provider  # noqa: F401  (ثبت درایور "mock")
import arya.providers.market.tsetmc_provider  # noqa: F401  (ثبت درایور "tsetmc")
from arya.risk.risk_manager import RiskManager
from arya.storage.cache import OHLCVStore
from arya.technical.indicator_engine import IndicatorEngine

logger = logging.getLogger(__name__)


class AryaApp:
    """Facade کلی برنامه - تمام لایه‌ها این‌جا Wire می‌شوند."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()
        self._configure_logging()

        self.store = OHLCVStore(self.settings.app["storage"]["path"])
        self.indicator_engine = IndicatorEngine(self.settings)
        self.technical_analyzer = TechnicalAnalyzer()
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
        # تنظیمات اختصاصی هر Provider فقط به همان Provider ارسال شود.
        if driver == "tsetmc" and "adjust" in cfg:
            kwargs["adjust"] = cfg["adjust"]
        return ProviderRegistry.create(driver, **kwargs)

    def analyze_symbol(self, ticker: str, market: str = "stock", timeframe: str = "1d") -> Recommendation:
        """اجرای کامل پایپ‌لاین برای یک نماد و برگرداندن Recommendation نهایی."""
        symbol = Symbol(ticker=ticker, market=market)

        # 1) Providers
        provider = self._provider_for_market(market)
        series = provider.fetch_ohlcv(symbol, timeframe=timeframe, limit=200)

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
        )

        return recommendation

    def list_symbols(self, market: str = "stock") -> list[Symbol]:
        return self._provider_for_market(market).list_symbols()
