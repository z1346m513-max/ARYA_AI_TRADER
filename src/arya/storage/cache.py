"""ذخیره OHLCV با پشتیبانی Cache-First و TTL."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from arya.models.market_data import Candle, OHLCVSeries, Symbol
from arya.storage.cache_metrics import cache_metrics


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    # SQLite datetime('now') بدون timezone
    if "T" not in value and " " in value:
        value = value.replace(" ", "T") + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class CacheLookup:
    series: OHLCVSeries | None
    hit: bool
    fresh: bool
    updated_at: datetime | None
    reason: str


class OHLCVStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ohlcv_cache (
                symbol TEXT NOT NULL,
                market TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (symbol, market, timeframe)
            )
            """
        )
        self._conn.commit()

    def get(
        self,
        symbol: Symbol,
        timeframe: str,
        *,
        ttl_seconds: int,
        min_candles: int | None = None,
    ) -> CacheLookup:
        row = self._conn.execute(
            "SELECT payload, updated_at FROM ohlcv_cache "
            "WHERE symbol=? AND market=? AND timeframe=?",
            (symbol.ticker, symbol.market, timeframe),
        ).fetchone()

        if not row:
            cache_metrics.record_miss("miss")
            return CacheLookup(None, False, False, None, "miss")

        payload_raw, updated_raw = row
        updated_at = _parse_utc(str(updated_raw))
        series = self._deserialize(symbol, timeframe, payload_raw)

        if ttl_seconds <= 0:
            cache_metrics.record_miss("disabled")
            return CacheLookup(series, True, False, updated_at, "disabled")

        age = (_utc_now() - updated_at).total_seconds()
        if age > ttl_seconds:
            cache_metrics.record_miss("stale_ttl")
            return CacheLookup(series, True, False, updated_at, "stale_ttl")

        if min_candles is not None and len(series.candles) < min_candles:
            cache_metrics.record_miss("stale_limit")
            return CacheLookup(series, True, False, updated_at, "stale_limit")

        cache_metrics.record_hit("fresh")
        return CacheLookup(series, True, True, updated_at, "fresh")

    def load(self, symbol: Symbol, timeframe: str) -> OHLCVSeries | None:
        """سازگاری با کد قدیمی — بدون ارزیابی TTL."""
        lookup = self.get(symbol, timeframe, ttl_seconds=10**9)
        return lookup.series if lookup.hit else None

    def save(self, series: OHLCVSeries) -> None:
        payload = json.dumps(
            [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in series.candles
            ]
        )
        self._conn.execute(
            """
            INSERT INTO ohlcv_cache (symbol, market, timeframe, payload, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(symbol, market, timeframe)
            DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at
            """,
            (
                series.symbol.ticker,
                series.symbol.market,
                series.timeframe,
                payload,
                _utc_now_iso(),
            ),
        )
        self._conn.commit()
        cache_metrics.record_save()

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _deserialize(symbol: Symbol, timeframe: str, payload: str) -> OHLCVSeries:
        raw = json.loads(payload)
        candles = [
            Candle(
                timestamp=datetime.fromisoformat(c["timestamp"]),
                open=c["open"],
                high=c["high"],
                low=c["low"],
                close=c["close"],
                volume=c["volume"],
            )
            for c in raw
        ]
        return OHLCVSeries(symbol=symbol, timeframe=timeframe, candles=candles)
