"""متریک hit-ratio کش OHLCV — thread-safe."""
from __future__ import annotations

import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class CacheMetricsSnapshot:
    hits: int
    misses: int
    stale: int
    force_refresh: int
    saves: int
    total_lookups: int
    hit_ratio: float
    by_reason: dict[str, int] = field(default_factory=dict)
    snapshot_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CacheMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._stale = 0
        self._force_refresh = 0
        self._saves = 0
        self._by_reason: dict[str, int] = {}

    def record_hit(self, reason: str = "fresh") -> None:
        with self._lock:
            self._hits += 1
            self._by_reason[reason] = self._by_reason.get(reason, 0) + 1

    def record_miss(self, reason: str = "miss") -> None:
        with self._lock:
            if reason.startswith("stale"):
                self._stale += 1
            else:
                self._misses += 1
            self._by_reason[reason] = self._by_reason.get(reason, 0) + 1

    def record_force_refresh(self) -> None:
        with self._lock:
            self._force_refresh += 1

    def record_save(self) -> None:
        with self._lock:
            self._saves += 1

    def snapshot(self) -> CacheMetricsSnapshot:
        with self._lock:
            total = self._hits + self._misses + self._stale
            ratio = (self._hits / total) if total else 0.0
            return CacheMetricsSnapshot(
                hits=self._hits,
                misses=self._misses,
                stale=self._stale,
                force_refresh=self._force_refresh,
                saves=self._saves,
                total_lookups=total,
                hit_ratio=round(ratio, 6),
                by_reason=dict(self._by_reason),
                snapshot_at=_utc_now_iso(),
            )

    def reset(self) -> None:
        with self._lock:
            self._hits = self._misses = self._stale = 0
            self._force_refresh = self._saves = 0
            self._by_reason.clear()


cache_metrics = CacheMetrics()
