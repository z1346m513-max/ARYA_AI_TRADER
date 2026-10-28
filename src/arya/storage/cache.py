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

from arya.data_quality import OHLCVQualityReport
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
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_quality_runs (
                run_id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                market TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                provider TEXT NOT NULL,
                retrieved_at_utc TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                first_timestamp TEXT,
                last_timestamp TEXT,
                snapshot_sha256 TEXT NOT NULL,
                is_valid INTEGER NOT NULL,
                issues_json TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def record_data_quality(
        self,
        run_id: str,
        series: OHLCVSeries,
        provider: str,
        retrieved_at_utc: str,
        report: OHLCVQualityReport,
        data_hash: str,
    ) -> None:
        """Append a validation result and normalized-input provenance record."""
        issues = [
            {"code": issue.code, "message": issue.message, "candle_index": issue.candle_index}
            for issue in report.issues
        ]
        self._conn.execute(
            """
            INSERT INTO data_quality_runs (
                run_id, ticker, market, timeframe, provider, retrieved_at_utc,
                row_count, first_timestamp, last_timestamp, snapshot_sha256,
                is_valid, issues_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                series.symbol.ticker,
                series.symbol.market,
                series.timeframe,
                provider,
                retrieved_at_utc,
                report.row_count,
                report.first_timestamp,
                report.last_timestamp,
                data_hash,
                int(report.is_valid),
                json.dumps(issues, ensure_ascii=False, sort_keys=True),
            ),
        )
        self._conn.commit()

    def load_data_quality_run(self, run_id: str) -> dict | None:
        """Return one recorded validation/provenance event, if it exists."""
        row = self._conn.execute(
            """SELECT run_id, ticker, market, timeframe, provider, retrieved_at_utc,
                      row_count, first_timestamp, last_timestamp, snapshot_sha256,
                      is_valid, issues_json
               FROM data_quality_runs WHERE run_id=?""",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        columns = (
            "run_id", "ticker", "market", "timeframe", "provider", "retrieved_at_utc",
            "row_count", "first_timestamp", "last_timestamp", "snapshot_sha256",
            "is_valid", "issues_json",
        )
        result = dict(zip(columns, row))
        result["is_valid"] = bool(result["is_valid"])
        result["issues"] = json.loads(result.pop("issues_json"))
        return result

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
