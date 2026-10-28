"""Data-quality checks for normalized market data before operational analysis.

These ARYA-owned checks validate structural OHLCV invariants only. They do not
claim that a feed is official, fresh, complete for an exchange calendar, or
suitable for an investment decision.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from arya.models.market_data import OHLCVSeries


@dataclass(frozen=True)
class QualityIssue:
    code: str
    message: str
    candle_index: int | None = None


@dataclass(frozen=True)
class OHLCVQualityReport:
    is_valid: bool
    row_count: int
    first_timestamp: str | None
    last_timestamp: str | None
    issues: tuple[QualityIssue, ...]


class OHLCVQualityError(ValueError):
    """Raised when a normalized OHLCV series violates required invariants."""

    def __init__(self, report: OHLCVQualityReport):
        self.report = report
        summary = "; ".join(issue.message for issue in report.issues)
        super().__init__(f"دادهٔ OHLCV برای تحلیل معتبر نیست: {summary}")


def validate_ohlcv_series(series: OHLCVSeries) -> OHLCVQualityReport:
    """Validate structural OHLCV invariants without network/calendar assumptions."""
    candles = series.candles
    issues: list[QualityIssue] = []
    if not candles:
        issues.append(QualityIssue("empty_series", "سری داده خالی است"))
        return OHLCVQualityReport(False, 0, None, None, tuple(issues))

    seen: set[datetime] = set()
    previous_timestamp: datetime | None = None
    for index, candle in enumerate(candles):
        timestamp = candle.timestamp
        if not isinstance(timestamp, datetime):
            issues.append(QualityIssue("invalid_timestamp", "زمان کندل از نوع datetime نیست", index))
        else:
            if timestamp in seen:
                issues.append(QualityIssue("duplicate_timestamp", "زمان کندل تکراری است", index))
            seen.add(timestamp)
            if previous_timestamp is not None:
                try:
                    if timestamp < previous_timestamp:
                        issues.append(QualityIssue("unordered_timestamp", "کندل‌ها به ترتیب زمانی صعودی نیستند", index))
                except TypeError:
                    issues.append(QualityIssue("incomparable_timestamp", "منطقهٔ زمانی timestampها با هم قابل مقایسه نیست", index))
            previous_timestamp = timestamp

        values = {
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
        }
        finite = True
        numeric: dict[str, float] = {}
        for field_name, value in values.items():
            try:
                number = float(value)
            except (TypeError, ValueError, OverflowError):
                finite = False
                issues.append(QualityIssue("non_numeric_" + field_name, f"فیلد {field_name} عددی نیست", index))
                continue
            if not math.isfinite(number):
                finite = False
                issues.append(QualityIssue("non_finite_" + field_name, f"فیلد {field_name} مقدار متناهی ندارد", index))
            numeric[field_name] = number
        if not finite:
            continue

        if min(numeric["open"], numeric["high"], numeric["low"], numeric["close"]) <= 0:
            issues.append(QualityIssue("non_positive_price", "قیمت‌های OHLC باید مثبت باشند", index))
        if numeric["volume"] < 0:
            issues.append(QualityIssue("negative_volume", "حجم معامله نمی‌تواند منفی باشد", index))
        if numeric["high"] < max(numeric["open"], numeric["close"], numeric["low"]):
            issues.append(QualityIssue("high_below_ohlc", "بیشینهٔ کندل از یکی از قیمت‌های OHLC کمتر است", index))
        if numeric["low"] > min(numeric["open"], numeric["close"], numeric["high"]):
            issues.append(QualityIssue("low_above_ohlc", "کمینهٔ کندل از یکی از قیمت‌های OHLC بیشتر است", index))

    first = candles[0].timestamp.isoformat() if isinstance(candles[0].timestamp, datetime) else None
    last = candles[-1].timestamp.isoformat() if isinstance(candles[-1].timestamp, datetime) else None
    return OHLCVQualityReport(not issues, len(candles), first, last, tuple(issues))


def snapshot_sha256(series: OHLCVSeries) -> str:
    """Hash the normalized observation deterministically for audit linkage."""
    payload = {
        "symbol": {"ticker": series.symbol.ticker, "market": series.symbol.market},
        "timeframe": series.timeframe,
        "candles": [
            {
                "timestamp": candle.timestamp.isoformat() if isinstance(candle.timestamp, datetime) else repr(candle.timestamp),
                "open": repr(candle.open),
                "high": repr(candle.high),
                "low": repr(candle.low),
                "close": repr(candle.close),
                "volume": repr(candle.volume),
            }
            for candle in series.candles
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
