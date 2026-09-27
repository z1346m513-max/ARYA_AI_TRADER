from datetime import datetime, timedelta, timezone

import pytest

from arya.models.market_data import Candle, OHLCVSeries, Symbol
from arya.storage.history_cache import (
    CacheStatus,
    SQLiteHistoryCache,
    make_history_cache_key,
)
from arya.storage.history_service import (
    MarketDataUnavailable,
    MarketHistoryService,
)


def _settings(tmp_path):
    from arya.config.settings import Settings

    settings = Settings.load()
    settings.app["storage"]["path"] = str(tmp_path / "arya.db")
    return settings


def _series(symbol="فملی", limit=3):
    base = datetime(2026, 9, 27, 9, 0)
    candles = [
        Candle(
            timestamp=base + timedelta(days=i),
            open=100 + i,
            high=105 + i,
            low=95 + i,
            close=102 + i,
            volume=1000 + i,
        )
        for i in range(limit)
    ]
    return OHLCVSeries(
        symbol=Symbol(ticker=symbol, market="stock"),
        timeframe="1d",
        candles=candles,
    )


class FakeProvider:
    name = "fake"

    def __init__(self, result=None, error=None):
        self.calls = 0
        self.result = result
        self.error = error

    def fetch_ohlcv(self, symbol, timeframe, limit=200):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result or _series(symbol, limit=min(limit, 3))


def test_cache_key_is_stable_and_excludes_limit():
    assert make_history_cache_key("tsetmc", "stock", " فملی ", "1d", False) == (
        "ohlcv:tsetmc:stock:فملی:1d:adjust=0"
    )
    assert make_history_cache_key("tsetmc", "stock", "فملی", "1d", False) == (
        "ohlcv:tsetmc:stock:فملی:1d:adjust=0"
    )


def test_fresh_cache_avoids_provider_call(tmp_path):
    settings = _settings(tmp_path)
    cache = SQLiteHistoryCache(settings.app["storage"]["path"])
    provider = FakeProvider(result=_series())
    service = MarketHistoryService(settings, cache, provider)
    now = datetime(2026, 9, 27, 8, 0, tzinfo=timezone.utc)

    first = service.get_or_refresh(
        Symbol("فملی", "stock"), now=now, limit=3
    )
    second = service.get_or_refresh(
        Symbol("فملی", "stock"),
        now=now + timedelta(seconds=30),
        limit=3,
    )

    assert first.refreshed is True
    assert second.status is CacheStatus.FRESH
    assert second.refreshed is False
    assert provider.calls == 1
    cache.close()


def test_off_session_cache_stays_fresh_for_longer(tmp_path):
    settings = _settings(tmp_path)
    cache = SQLiteHistoryCache(settings.app["storage"]["path"])
    provider = FakeProvider(result=_series())
    service = MarketHistoryService(settings, cache, provider)
    now = datetime(2026, 9, 27, 5, 0, tzinfo=timezone.utc)

    service.get_or_refresh(Symbol("فملی", "stock"), now=now)
    result = service.get_or_refresh(
        Symbol("فملی", "stock"),
        now=now + timedelta(hours=5),
        limit=3,
    )

    assert result.status is CacheStatus.FRESH
    assert result.refreshed is False
    assert provider.calls == 1
    cache.close()


def test_stale_cache_refresh_failure_serves_stale(tmp_path):
    settings = _settings(tmp_path)
    cache = SQLiteHistoryCache(settings.app["storage"]["path"])
    good = FakeProvider(result=_series())
    service = MarketHistoryService(settings, cache, good)
    now = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)
    service.get_or_refresh(Symbol("فملی", "stock"), now=now)

    failing = FakeProvider(error=TimeoutError("TSETMC timeout"))
    stale_service = MarketHistoryService(settings, cache, failing)
    result = stale_service.get_or_refresh(
        Symbol("فملی", "stock"),
        now=now + timedelta(hours=8),
    )

    assert result.status is CacheStatus.STALE
    assert result.refreshed is False
    assert result.warning is not None
    assert failing.calls == 1
    cache.close()


def test_expired_cache_refresh_failure_fails_closed(tmp_path):
    settings = _settings(tmp_path)
    cache = SQLiteHistoryCache(settings.app["storage"]["path"])
    service = MarketHistoryService(
        settings, cache, FakeProvider(result=_series())
    )
    now = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)
    service.get_or_refresh(Symbol("فملی", "stock"), now=now)

    failing = FakeProvider(error=TimeoutError("TSETMC timeout"))
    expired_service = MarketHistoryService(settings, cache, failing)
    with pytest.raises(MarketDataUnavailable):
        expired_service.get_or_refresh(
            Symbol("فملی", "stock"),
            now=now + timedelta(days=3),
        )
    cache.close()


def test_stale_entry_is_refreshed_successfully(tmp_path):
    settings = _settings(tmp_path)
    cache = SQLiteHistoryCache(settings.app["storage"]["path"])
    initial = FakeProvider(result=_series(limit=3))
    service = MarketHistoryService(settings, cache, initial)
    now = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)
    service.get_or_refresh(Symbol("فملی", "stock"), now=now)

    refreshed = FakeProvider(result=_series(limit=3))
    service2 = MarketHistoryService(settings, cache, refreshed)
    result = service2.get_or_refresh(
        Symbol("فملی", "stock"),
        now=now + timedelta(hours=8),
    )

    assert result.status is CacheStatus.FRESH
    assert result.refreshed is True
    assert refreshed.calls == 1
    cache.close()


def test_small_limit_reuses_larger_fresh_cache(tmp_path):
    settings = _settings(tmp_path)
    cache = SQLiteHistoryCache(settings.app["storage"]["path"])
    provider = FakeProvider(result=_series(limit=3))
    service = MarketHistoryService(settings, cache, provider)
    now = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)

    service.get_or_refresh(Symbol("فملی", "stock"), now=now, limit=3)
    result = service.get_or_refresh(
        Symbol("فملی", "stock"),
        now=now + timedelta(seconds=20),
        limit=2,
    )

    assert result.status is CacheStatus.FRESH
    assert len(result.series.candles) == 2
    assert provider.calls == 1
    cache.close()

def test_refresh_cached_keys_skips_fresh_entries(tmp_path):
    settings = _settings(tmp_path)
    cache = SQLiteHistoryCache(settings.app["storage"]["path"])
    provider = FakeProvider(result=_series())
    service = MarketHistoryService(settings, cache, provider)
    now = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)

    service.get_or_refresh(Symbol("فملی", "stock"), now=now)
    results = service.refresh_cached_keys(
        market="stock",
        limit=3,
        now=now + timedelta(seconds=30),
    )

    assert results == []
    assert provider.calls == 1
    cache.close()


def test_refresh_cached_keys_refreshes_stale_entries(tmp_path):
    settings = _settings(tmp_path)
    cache = SQLiteHistoryCache(settings.app["storage"]["path"])
    initial = FakeProvider(result=_series())
    service = MarketHistoryService(settings, cache, initial)
    now = datetime(2026, 9, 27, 6, 0, tzinfo=timezone.utc)

    service.get_or_refresh(Symbol("فملی", "stock"), now=now)

    refreshed = FakeProvider(result=_series())
    service2 = MarketHistoryService(settings, cache, refreshed)
    results = service2.refresh_cached_keys(
        market="stock",
        limit=3,
        now=now + timedelta(hours=8),
    )

    assert len(results) == 1
    assert results[0].refreshed is True
    assert refreshed.calls == 1
    cache.close()


def test_cache_migrates_legacy_schema(tmp_path):
    import sqlite3

    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE ohlcv_history_cache (
            cache_key TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            market TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            adjusted INTEGER NOT NULL DEFAULT 0,
            payload TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            last_candle_at TEXT,
            last_error TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    cache = SQLiteHistoryCache(db_path)
    columns = {
        row[1]
        for row in cache._conn.execute(
            "PRAGMA table_info(ohlcv_history_cache)"
        ).fetchall()
    }
    assert "provider" in columns
    assert cache.keys() == []
    cache.close()
