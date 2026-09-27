"""Smart cache-aside and automatic refresh service for market history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from arya.config.settings import Settings
from arya.models.market_data import OHLCVSeries, Symbol
from arya.providers.base import MarketDataProvider
from arya.storage.history_cache import (
    CacheRecord,
    CacheStatus,
    SQLiteHistoryCache,
    make_history_cache_key,
    utc_now,
)


class MarketDataUnavailable(RuntimeError):
    """Raised when no usable cache remains and the provider cannot refresh."""


@dataclass(frozen=True)
class CachePolicy:
    fresh_ttl: timedelta
    stale_grace: timedelta
    outside_session_ttl: timedelta
    outside_session_stale_grace: timedelta

    @classmethod
    def from_settings(cls, settings: Settings, market: str) -> "CachePolicy":
        cache_cfg = settings.scheduler.get("history_cache", {}).get(market, {})
        return cls(
            fresh_ttl=timedelta(
                seconds=float(cache_cfg.get("fresh_ttl_seconds", 60))
            ),
            stale_grace=timedelta(
                seconds=float(cache_cfg.get("stale_grace_seconds", 900))
            ),
            outside_session_ttl=timedelta(
                seconds=float(
                    cache_cfg.get("outside_session_ttl_seconds", 21600)
                )
            ),
            outside_session_stale_grace=timedelta(
                seconds=float(
                    cache_cfg.get("outside_session_stale_grace_seconds", 172800)
                )
            ),
        )


class MarketSession:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timezone = ZoneInfo(
            settings.app.get("timezone", "Asia/Tehran")
        )

    def is_open(self, market: str, now: datetime) -> bool:
        cfg = self.settings.scheduler.get("markets", {}).get(market, {})
        if not cfg.get("market_hours_only", False):
            return True

        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        local = now.astimezone(self.timezone)
        start = time.fromisoformat(cfg.get("open_time", "09:00"))
        close = time.fromisoformat(cfg.get("close_time", "12:30"))
        return start <= local.time() <= close


@dataclass(frozen=True)
class HistoryResult:
    series: OHLCVSeries
    status: CacheStatus
    refreshed: bool
    fetched_at: datetime
    age_seconds: float
    warning: str | None = None


class MarketHistoryService:
    """Serve cached history and refresh according to an explicit stale policy."""

    def __init__(
        self,
        settings: Settings,
        cache: SQLiteHistoryCache,
        provider: MarketDataProvider,
    ):
        self.settings = settings
        self.cache = cache
        self.provider = provider
        self.session = MarketSession(settings)

    def _status(
        self,
        record: CacheRecord,
        market: str,
        now: datetime,
    ) -> tuple[CacheStatus, float]:
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        fetched = record.fetched_at
        age = max(0.0, (now - fetched).total_seconds())
        policy = CachePolicy.from_settings(self.settings, market)
        in_session = self.session.is_open(market, now)
        fresh_ttl = (
            policy.fresh_ttl if in_session else policy.outside_session_ttl
        )
        stale_grace = (
            policy.stale_grace
            if in_session
            else policy.outside_session_stale_grace
        )

        if age <= fresh_ttl.total_seconds():
            return CacheStatus.FRESH, age
        if age <= (fresh_ttl + stale_grace).total_seconds():
            return CacheStatus.STALE, age
        return CacheStatus.EXPIRED, age

    def _trim(
        self,
        series: OHLCVSeries,
        limit: int,
    ) -> OHLCVSeries:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        if len(series.candles) <= limit:
            return series
        return OHLCVSeries(
            symbol=series.symbol,
            timeframe=series.timeframe,
            candles=series.candles[-limit:],
        )

    def get_or_refresh(
        self,
        symbol: Symbol,
        *,
        timeframe: str = "1d",
        limit: int = 200,
        adjust: bool = False,
        now: datetime | None = None,
    ) -> HistoryResult:
        now = now or utc_now()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        key = make_history_cache_key(
            symbol.market, symbol.ticker, timeframe, adjust
        )
        record = self.cache.load(key)

        if record is not None:
            status, age = self._status(record, symbol.market, now)
            if status is CacheStatus.FRESH and len(record.series.candles) >= limit:
                return HistoryResult(
                    series=self._trim(record.series, limit),
                    status=status,
                    refreshed=False,
                    fetched_at=record.fetched_at,
                    age_seconds=age,
                )

        previous = record
        try:
            fresh_series = self.provider.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=limit,
            )
            saved = self.cache.save(
                fresh_series,
                adjusted=adjust,
                fetched_at=now,
                cache_key=key,
            )
            return HistoryResult(
                series=saved.series,
                status=CacheStatus.FRESH,
                refreshed=True,
                fetched_at=saved.fetched_at,
                age_seconds=0.0,
            )
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            self.cache.mark_error(key, message)
            if previous is not None:
                status, age = self._status(previous, symbol.market, now)
                if status is CacheStatus.STALE:
                    return HistoryResult(
                        series=self._trim(previous.series, limit),
                        status=status,
                        refreshed=False,
                        fetched_at=previous.fetched_at,
                        age_seconds=age,
                        warning=(
                            "TSETMC refresh failed; serving stale cached data: "
                            f"{message}"
                        ),
                    )
            raise MarketDataUnavailable(
                f"No usable market history for {symbol.ticker}: {message}"
            ) from exc

    def refresh_cached_keys(
        self,
        *,
        market: str = "stock",
        limit: int = 200,
        now: datetime | None = None,
    ) -> list[HistoryResult]:
        """Refresh cache entries due now; intended for the scheduler."""
        current = now or utc_now()
        results: list[HistoryResult] = []

        for key in self.cache.keys(market):
            record = self.cache.load(key)
            if record is None:
                continue
            status, _ = self._status(record, market, current)
            if status is CacheStatus.FRESH and len(record.series.candles) >= limit:
                continue

            results.append(
                self.get_or_refresh(
                    record.series.symbol,
                    timeframe=record.series.timeframe,
                    limit=limit,
                    now=current,
                )
            )
        return results
