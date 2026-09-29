# ARCH-009 — Provider Interfaces & Normalized External Data Schemas

## Purpose
Define stable provider-neutral contracts for TSETMC, Codal, Whale Alert, and CCXT. This layer handles read-only ingestion only and must not execute trades.

## Common contracts
### DataProvenance
Required fields: provider, provider_version, source_type, source_endpoint, source_reference, observed_at, published_at, retrieved_at, request_id, correlation_id, session_id, schema_version.

### Freshness
Required fields: observed_at, retrieved_at, max_age_seconds, age_seconds, status (FRESH | STALE | UNKNOWN), quality (VALID | PARTIAL | INVALID | UNAVAILABLE).

### ProviderResult[T]
Contains: data, provenance, freshness, warnings, error.

### ProviderError
Required fields: code, message, retryable, http_status, provider_code, occurred_at.
Recommended error codes: AUTHENTICATION_FAILED, AUTHORIZATION_FAILED, RATE_LIMITED, TIMEOUT, NETWORK_UNAVAILABLE, PROVIDER_UNAVAILABLE, MALFORMED_RESPONSE, SCHEMA_MISMATCH, INVALID_REQUEST, NOT_FOUND, STALE_DATA, PARTIAL_DATA, DATA_QUALITY_FAILURE, CONFIGURATION_ERROR, INTERNAL_ADAPTER_ERROR.
Retry only explicitly retryable failures, with exponential backoff and jitter. Respect Retry-After. Do not blindly retry authentication, invalid-request, or schema failures. Preserve original error and retry count. Use circuit breaking after repeated provider failures.

### RateLimitState
requests_remaining, limit, reset_at, retry_after_seconds, scope.

## Provider interfaces
### TSETMCProvider
fetch_instruments(), fetch_market_watch(), fetch_ohlcv(symbol, timeframe, start, end), fetch_market_flow(symbol, start, end), fetch_shareholders(symbol).

### CodalProvider
search_issuers(query), list_reports(issuer_id, filters), fetch_report(report_id).

### WhaleAlertProvider
stream_transfers(filters), get_transfer(tx_hash), get_wallet_profile(address, chain).

### CCXTMarketProvider
fetch_ticker(exchange, symbol), fetch_order_book(exchange, symbol, depth), fetch_ohlcv(exchange, symbol, timeframe, start, end).

## Normalized schemas
### Market candle
symbol, market, timeframe, timestamp, open, high, low, close, volume, quote_volume, currency, provenance, freshness.

### TSETMC Iranian instrument
instrument_id, ticker, name, market, industry_code, base_currency, active, provenance.

### Market flow
symbol, date, individual_buy_value, individual_sell_value, institutional_buy_value, institutional_sell_value, buy_count, sell_count, provenance, freshness.

### Codal issuer/report
Issuer: issuer_id, symbol, name, national_identifier.
Report: report_id, issuer_id, report_type, title, published_at, period_end, source_reference, provenance.
Normalized report: report, facts, currency, unit, extraction_status (STRUCTURED | PARSED | PARTIAL), provenance, freshness.

### Whale transfer
tx_hash, chain, block_number, observed_at, asset, amount, usd_value, from_address, to_address, from_label, to_label, transaction_type, confirmation_status, provenance, freshness.

### Wallet profile
address, chain, label, entity_type (EXCHANGE | INSTITUTION | SMART_MONEY | UNKNOWN | OTHER), confidence, provenance.
A large transfer is not automatically a whale, smart-money event, or bullish/bearish signal. Transaction size, entity identity, classification confidence, and trading interpretation remain separate fields/layers.

### CCXT ticker
exchange, symbol, timestamp, bid, ask, last, base_volume, quote_volume, provenance, freshness.

### CCXT order book
exchange, symbol, timestamp, bids, asks, provenance, freshness.

## Provider-specific validation
### TSETMC
Treat 403/geo-blocking as explicit provider failure. Keep User-Agent and provider-specific configuration isolated. Model holidays and trading halts. Preserve adjusted/unadjusted semantics. Detect duplicate/versioned instruments. Missing data must never be interpreted as zero.

### Codal
Preserve publication timestamp separately from reporting period. Preserve currency and units. Detect duplicate/versioned reports. Parsing failures become PARTIAL or INVALID, never silently valid.

### Whale Alert
Preserve chain, transaction hash, block, addresses, labels, and confirmation state. Do not infer trading direction from transfer size alone.

### CCXT
Normalize exchange-specific symbols. Record exchange ID and CCXT version. Distinguish REST and WebSocket provenance. Model exchange rate limits and timestamp/nonce/signature failures. Keep market-data credentials separate from trading credentials.

## Pipeline boundary
External Source → Provider Adapter → Raw Response → Normalization → Schema Validation → Data Quality → Freshness → Provider State/Rate Limits → Cache/Storage → Session/Event → Analysis/Scoring/AI → Risk → Recommendation
Provider adapters must not directly invoke AI, risk decisions, or order execution.

## Provider health and failure state
HEALTHY → DEGRADED → OPEN → HALF_OPEN → HEALTHY.
Data availability: DATA_AVAILABLE, DATA_PARTIAL, DATA_STALE, DATA_UNAVAILABLE.
No provider outage may silently become valid data, and no provider should be silently substituted.

## Contract testing
Required tests: valid normalization; provenance/freshness propagation; missing/malformed/duplicate/timestamp/symbol/unit validation; stale/partial data; timeout/network/auth/403/429/5xx/schema failures; retry/backoff and circuit breaker; rate-limit state; reconnect and duplicate event handling.

## Security and reproducibility
Never place API keys, tokens, private keys, broker credentials, or other secrets in normalized records, logs, Session events, fixtures, screenshots, or source control.
For reproducibility record Session ID, Git SHA, provider/version, schema version, configuration version, source reference, and retrieval timestamp. Backtests additionally record dataset version, time range, timeframe, fees, slippage, and adjustment policy.

## Traceability
Related issues: #29 DATA-001, #31 RISK-001, #33 QA-001, #34 SEC-OPS-001, #38 PLAN-001, #39 PLAN-002, #40 DATA-002, #41 ARCH-009.

## Implementation order
1. Common ProviderResult/Provenance/Freshness
2. ProviderError + RateLimitState
3. TSETMC adapter
4. Codal adapter
5. CCXT adapter
6. Whale Alert adapter
7. Contract tests
8. Provider health/circuit breaker
9. Session/Event integration
10. Analysis/AI integration

## Definition of Done
Implementation, tests, documentation, architecture/config/data impact notes, reproducibility evidence, and a reviewable PR. No live trading execution is introduced by this work package.