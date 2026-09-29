"""Read-only, provider-neutral external data contracts."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Generic, Literal, Protocol, Sequence, TypeVar

T = TypeVar("T")
class FreshnessStatus(str, Enum): FRESH="FRESH"; STALE="STALE"; UNKNOWN="UNKNOWN"
class DataQuality(str, Enum): VALID="VALID"; PARTIAL="PARTIAL"; INVALID="INVALID"; UNAVAILABLE="UNAVAILABLE"
class DataAvailability(str, Enum): AVAILABLE="DATA_AVAILABLE"; PARTIAL="DATA_PARTIAL"; STALE="DATA_STALE"; UNAVAILABLE="DATA_UNAVAILABLE"
class ProviderErrorCode(str, Enum):
    AUTHENTICATION_FAILED="AUTHENTICATION_FAILED"; AUTHORIZATION_FAILED="AUTHORIZATION_FAILED"; RATE_LIMITED="RATE_LIMITED"; TIMEOUT="TIMEOUT"; NETWORK_UNAVAILABLE="NETWORK_UNAVAILABLE"; PROVIDER_UNAVAILABLE="PROVIDER_UNAVAILABLE"; MALFORMED_RESPONSE="MALFORMED_RESPONSE"; SCHEMA_MISMATCH="SCHEMA_MISMATCH"; INVALID_REQUEST="INVALID_REQUEST"; NOT_FOUND="NOT_FOUND"; STALE_DATA="STALE_DATA"; PARTIAL_DATA="PARTIAL_DATA"; DATA_QUALITY_FAILURE="DATA_QUALITY_FAILURE"; CONFIGURATION_ERROR="CONFIGURATION_ERROR"; INTERNAL_ADAPTER_ERROR="INTERNAL_ADAPTER_ERROR"
class CircuitBreakerState(str, Enum): CLOSED="CLOSED"; OPEN="OPEN"; HALF_OPEN="HALF_OPEN"

@dataclass(frozen=True)
class DataProvenance:
    provider: str; source_type: Literal["REST","WEBSOCKET","API","PROXY","FILE"]; retrieved_at: datetime; schema_version: str
    provider_version: str|None=None; source_endpoint: str|None=None; source_reference: str|None=None; observed_at: datetime|None=None; published_at: datetime|None=None; request_id: str|None=None; correlation_id: str|None=None; session_id: str|None=None
    def __post_init__(self):
        if not self.provider.strip() or not self.schema_version.strip(): raise ValueError("provider and schema_version are required")
        if self.retrieved_at.tzinfo is None: raise ValueError("retrieved_at must be timezone-aware")

@dataclass(frozen=True)
class Freshness:
    observed_at: datetime|None; retrieved_at: datetime; max_age_seconds: int|None; age_seconds: float|None; status: FreshnessStatus; quality: DataQuality
    def __post_init__(self):
        if self.retrieved_at.tzinfo is None: raise ValueError("retrieved_at must be timezone-aware")
        if any(v is not None and v < 0 for v in (self.max_age_seconds,self.age_seconds)): raise ValueError("ages must be non-negative")
    @classmethod
    def unknown(cls, retrieved_at=None): return cls(None,retrieved_at or datetime.now(timezone.utc),None,None,FreshnessStatus.UNKNOWN,DataQuality.UNAVAILABLE)

@dataclass(frozen=True)
class ProviderError:
    code: ProviderErrorCode; message: str; retryable: bool; occurred_at: datetime; http_status: int|None=None; provider_code: str|None=None
    def __post_init__(self):
        if self.occurred_at.tzinfo is None: raise ValueError("occurred_at must be timezone-aware")
@dataclass(frozen=True)
class RateLimitState: requests_remaining: int|None=None; limit: int|None=None; reset_at: datetime|None=None; retry_after_seconds: float|None=None; scope: str|None=None
@dataclass(frozen=True)
class ProviderHealth:
    provider: str; connected: bool; authenticated: bool|None; last_success_at: datetime|None; consecutive_failures: int; circuit_breaker_state: CircuitBreakerState; rate_limit: RateLimitState|None=None; last_error_code: ProviderErrorCode|None=None
@dataclass(frozen=True)
class ProviderResult(Generic[T]):
    data: T|None; provenance: DataProvenance; freshness: Freshness; warnings: tuple[str,...]=field(default_factory=tuple); error: ProviderError|None=None
    def __post_init__(self):
        if self.error is not None and self.data is not None: raise ValueError("a failed result must not contain data")
        if self.error is None and self.data is None: raise ValueError("a successful result must contain data")
    @property
    def available(self):
        if self.error or self.freshness.quality is DataQuality.UNAVAILABLE: return DataAvailability.UNAVAILABLE
        if self.freshness.status is FreshnessStatus.STALE: return DataAvailability.STALE
        if self.freshness.quality is DataQuality.PARTIAL: return DataAvailability.PARTIAL
        return DataAvailability.AVAILABLE
@dataclass(frozen=True)
class NormalizedCandle:
    symbol: str; market: Literal["stock","crypto","forex"]; timeframe: str; timestamp: datetime; open: Decimal; high: Decimal; low: Decimal; close: Decimal; volume: Decimal; quote_volume: Decimal|None; currency: str|None; provenance: DataProvenance; freshness: Freshness
    def __post_init__(self):
        if self.timestamp.tzinfo is None: raise ValueError("timestamp must be timezone-aware")
        if self.high < max(self.open,self.close) or self.low > min(self.open,self.close): raise ValueError("candle high/low are inconsistent")
        if self.volume < 0: raise ValueError("volume must be non-negative")
class ReadOnlyMarketProvider(Protocol):
    name: str
    def health(self) -> ProviderResult[ProviderHealth]: ...
    def list_symbols(self) -> ProviderResult[Sequence[str]]: ...
    def fetch_ohlcv(self, symbol: str, timeframe: str, *, start: datetime|None=None, end: datetime|None=None, limit: int|None=None) -> ProviderResult[Sequence[NormalizedCandle]]: ...
