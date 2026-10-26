# Development note — M2 smart_money offline path (2026-10-23)

Branch: `feat/m2-smart-money-offline`

## Implemented
- `ShareholderFlowMetrics` model (`src/arya/models/shareholders.py`)
- `ShareholderDataProvider` + separate registry (`shareholder_base.py`)
- `MockShareholderProvider` with ACCUM / DIST / missing fixtures
- `ShareChangeAnalyzer` → `SectionScore(section="smart_money")`
- `configs/smart_money.yaml` + `providers.yaml` shareholders: mock
- Offline tests: `tests/analysis/test_share_change_analyzer.py`
- Daily ingest skeleton: `operations/daily_ingest.py` + `configs/daily_ingest.yaml`

## Explicit non-claims
- No SOAP/REST ShareChange live driver
- No ONLINE_VERIFIED for major shareholders
- Thresholds are provisional
- Bootstrap wire to scoring may need merge of local `bootstrap.py` if not in this branch tip

## How to test offline
```bash
pip install -e ".[dev]"
pytest tests/analysis/test_share_change_analyzer.py -q
```

## Next
1. Phase 0: real ShareChange/ClientType samples from Iran IP
2. Wire bootstrap fully if missing on merge
3. Feature-flag default `smart_money.enabled: false` until before/after score comparison
