"""قرارداد کیفیت و تازگی داده برای همه‌ی منابع ARYA AI Trader."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class DataStatus(str, Enum):
    LIVE = "live"
    FRESH = "fresh"
    STALE = "stale"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    SYNTHETIC = "synthetic"


class DataQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DataProvenance:
    """منبع، زمان دریافت و وضعیت داده را به خروجی تحلیل متصل می‌کند."""

    source: str
    status: DataStatus
    quality: DataQuality = DataQuality.UNKNOWN
    fetched_at: datetime | None = None
    as_of: datetime | None = None
    error: str | None = None

    @property
    def age_seconds(self) -> float | None:
        if self.fetched_at is None:
            return None
        now = datetime.now(timezone.utc)
        fetched = self.fetched_at
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        return max(0.0, (now - fetched).total_seconds())


@dataclass(frozen=True)
class DataCoverage:
    """پوشش داده‌ی بخش‌های مختلف تحلیل؛ نبود داده نباید با confidence بالا اشتباه شود."""

    available: tuple[str, ...] = ()
    unavailable: tuple[str, ...] = ()

    @property
    def ratio(self) -> float:
        total = len(self.available) + len(self.unavailable)
        return len(self.available) / total if total else 0.0
