"""Smart TTL cache for market OHLCV history.

The cache is provider-agnostic. It stores fetch metadata separately from the
OHLCV contract so refresh policy can evolve without coupling analysis layers
to TSETMC.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import json
import sqlite3

from arya.models.market_data import Candle, OHLCVSeries, Symbol


class CacheStatus(str, Enum):
    MISS = "miss"
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"


@dataclass(frozen=True)
class CacheRecord:
    key: str
    series: OHLCVSeries
    fetched_at: datetime
    last_candle_at: datetime | None
    last_error: str | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_ticker(ticker: str) -> str:
    value = " ".join(ticker.strip().split())
    if not value:
        raise ValueError("ticker must not be empty")
    return value.replace(":", "%3A")


def make_history_cache_key(
    market: str,
    ticker: str,
    timeframe: str,
    adjust: bool = False,
) -> str:
    """Build a stable key; request limit is intentionally excluded."""
    return (
        f"ohlcv:{market.strip().lower()}:{normalize_ticker(ticker)}:"
        f"{timeframe.strip().lower()}:adjust={int(bool(adjust))}"
    )


class SQLiteHistoryCache:
    """SQLite-backed cache with explicit fetch metadata and refresh state."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ohlcv_history_cache (
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
        self._conn.commit()

    def save(
        self,
        series: OHLCVSeries,
        *,
        adjusted: bool = False,
        fetched_at: datetime | None = None,
        cache_key: str | None = None,
    ) -> CacheRecord:
        fetched_at = fetched_at or utc_now()
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        key = cache_key or make_history_cache_key(
            series.symbol.market,
            series.symbol.ticker,
            series.timeframe,
            adjusted,
        )
        payload = json.dumps(
            [
                {
                    "timestamp": candle.timestamp.isoformat(),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                }
                for candle in series.candles
            ]
        )
        last_candle_at = series.candles[-1].timestamp if series.candles else None
        self._conn.execute(
            """
            INSERT INTO ohlcv_history_cache
                (cache_key, symbol, market, timeframe, adjusted, payload,
                 fetched_at, last_candle_at, last_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload=excluded.payload,
                fetched_at=excluded.fetched_at,
                last_candle_at=excluded.last_candle_at,
                last_error=NULL
            """,
            (
                key,
                series.symbol.ticker,
                series.symbol.market,
                series.timeframe,
                int(adjusted),
                payload,
                fetched_at.isoformat(),
                last_candle_at.isoformat() if last_candle_at else None,
            ),
        )
        self._conn.commit()
        return CacheRecord(
            key=key,
            series=series,
            fetched_at=fetched_at,
            last_candle_at=last_candle_at,
        )

    def load(self, key: str) -> CacheRecord | None:
        row = self._conn.execute(
            """
            SELECT cache_key, symbol, market, timeframe, payload,
                   fetched_at, last_candle_at, last_error
            FROM ohlcv_history_cache
            WHERE cache_key=?
            """,
            (key,),
        ).fetchone()
        if row is None:
            return None

        raw = json.loads(row[4])
        candles = [
            Candle(
                timestamp=datetime.fromisoformat(item["timestamp"]),
                open=item["open"],
                high=item["high"],
                low=item["low"],
                close=item["close"],
                volume=item["volume"],
            )
            for item in raw
        ]
        fetched_at = datetime.fromisoformat(row[5])
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        last_candle_at = (
            datetime.fromisoformat(row[6]) if row[6] else None
        )
        symbol = Symbol(ticker=row[1], market=row[2])
        series = OHLCVSeries(symbol=symbol, timeframe=row[3], candles=candles)
        return CacheRecord(
            key=row[0],
            series=series,
            fetched_at=fetched_at,
            last_candle_at=last_candle_at,
            last_error=row[7],
        )

    def mark_error(self, key: str, error: str) -> None:
        self._conn.execute(
            "UPDATE ohlcv_history_cache SET last_error=? WHERE cache_key=?",
            (error[:1000], key),
        )
        self._conn.commit()

    def keys(self, market: str | None = None) -> list[str]:
        if market:
            rows = self._conn.execute(
                "SELECT cache_key FROM ohlcv_history_cache WHERE market=? ORDER BY cache_key",
                (market,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT cache_key FROM ohlcv_history_cache ORDER BY cache_key"
            ).fetchall()
        return [row[0] for row in rows]

    def close(self) -> None:
        self._conn.close()
