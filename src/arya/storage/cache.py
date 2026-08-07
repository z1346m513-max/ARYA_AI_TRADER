"""
لایه‌ی ذخیره‌سازی. مسئولیت این ماژول کش کردن داده‌ی دریافتی از Providerها
و جلوگیری از فراخوانی مکرر API است. Backend پیش‌فرض SQLite است (سبک، بدون
نیاز به سرویس جداگانه)؛ در آینده می‌توان Postgres را جایگزین کرد بدون تغییر
در امضای متدهای این کلاس.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from arya.models.market_data import Candle, OHLCVSeries, Symbol


class OHLCVStore:
    """ذخیره و بازیابی سری‌های OHLCV در SQLite."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
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
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(symbol, market, timeframe)
            DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at
            """,
            (series.symbol.ticker, series.symbol.market, series.timeframe, payload),
        )
        self._conn.commit()

    def load(self, symbol: Symbol, timeframe: str) -> OHLCVSeries | None:
        from datetime import datetime

        row = self._conn.execute(
            "SELECT payload FROM ohlcv_cache WHERE symbol=? AND market=? AND timeframe=?",
            (symbol.ticker, symbol.market, timeframe),
        ).fetchone()
        if not row:
            return None
        raw = json.loads(row[0])
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

    def close(self) -> None:
        self._conn.close()
