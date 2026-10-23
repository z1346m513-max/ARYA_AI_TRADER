# Mapping: pytse-client vs ARYA_AI_TRADER layers

**Source reviewed:** https://github.com/Glyphack/pytse-client (README)
**Date:** 2026-10-23
**Integration status:** Proposed / evaluation only — not an official project driver yet
**Source type:** Secondary / unofficial client over public TSETMC data

## Integration principles

- Analyzers and Scoring must **not** import `pytse_client` directly.
- Only via Provider + internal models (`OHLCVSeries`, `ShareholderFlowMetrics`, ...).
- Until Iran-IP evidence is logged in the data matrix: `NOT_TESTED` or at most `ONLINE_PARTIAL`.

## Capability mapping

| pytse-client capability | ARYA layer | Suggested contract | Priority | Risk / note |
|-------------------------|------------|--------------------|----------|-------------|
| `download` / OHLCV history | Market Provider | `MarketDataProvider.fetch_ohlcv` | Medium | Overlaps `TsetmcMarketProvider`; fallback or replace only after benchmark |
| Realtime symbol quote | Market Provider | `fetch_market_watch` / quote | Medium | Endpoint stability |
| Financial indexes | Market / macro | Separate index model or series | Low | Not critical for M1 |
| Client types (retail/legal) | Shareholder / smart_money | `ShareholderFlowMetrics` legal/individual fields | **High** | Closest fit to ShareChangeAnalyzer inputs |
| Major shareholders + history | Shareholder Provider | Ownership model (distinct from shareholder *count*) | **High** | Aligns with ShareHolderChanges page; lock field meaning with real samples |
| Share count history | Shareholder / fundamentals | Optional model field | Medium | Not the same as “number of shareholders” |
| Free float | fundamentals / risk | float_shares field | Medium | |
| Orderbook | Market depth (future) | Separate depth model | Low now | Not needed for M1 |
| Trade details / ticks | microstructure (future) | — | Low | High volume / rate limits |
| EPS / P/E / base volume | FundamentalMetrics | Partial fundamentals fill | Medium | Not a full Codal replacement |
| Filter-writing stats | scanner / filters | `MarketFilterConfig` inputs | Medium | |
| CSV export | operations / ingest | `data/snapshots/` | Low | Do not commit daily dumps |

## Not covered by pytse (need other sources)

| ARYA need | Alternative |
|-----------|-------------|
| Structured disclosures / statements | Codal provider |
| Fund/PM lists, CFI licenses | Manual seed + official sources |
| Official SOAP/REST with verified contract | Phase-0 on service/api.tsetmc.com |
| Uptime / schema SLA | None for unofficial clients |

## Suggested integration path (no conflict with current code)

1. **Evaluation:** optional `scripts/probe_pytse_client.py` on Iran network; store samples under `docs/sources/samples/`.
2. **Provider:** e.g. `PytseShareholderProvider` via `@ShareholderProviderRegistry.register("pytse")`; YAML default stays `mock`.
3. **Do not** replace `TsetmcMarketProvider` immediately for OHLCV.
4. Review **LICENSE** before commercial redistribution.

## Relation to CR-20261024-001

- Compatible with D1 (internal model) and D2 (separate provider).
- Compatible with D3 (mock default): pytse is an optional later driver.
- Does **not** replace official SOAP/REST phase-0 evidence; at most parallel discovery / fallback.
