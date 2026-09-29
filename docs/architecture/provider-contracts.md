# Provider Contracts v1

`arya.providers.contracts` is the required read-only boundary between external sources and core analysis.

## Non-negotiable rules

- Adapters normalize raw payloads before returning them to core code.
- Every public adapter result is a `ProviderResult` with provenance and freshness.
- A failure is `data=None, error=...`, never an empty collection.
- Store and compare timezone-aware timestamps in UTC.
- Preserve missing values; do not replace them with zero.
- Do not treat `STALE`, `PARTIAL`, or `UNAVAILABLE` as current valid data.
- Do not store keys, tokens, or trading credentials in models, logs, fixtures, or commits.
- This contract is read-only: it cannot place orders.

## Migration

1. Implement `ReadOnlyMarketProvider` per adapter.
2. Return `ProviderResult` from every public call.
3. Map source payloads to `NormalizedCandle` or another normalized domain model.
4. Gate analysis and recommendations on `result.available`.
5. Add tests for valid, partial, stale, timeout, 403, 429, malformed, and schema-change responses.

Adapters should use local rate limits, retry only transient failures with backoff and jitter, honor `Retry-After`, and open a circuit breaker after repeated failures.
