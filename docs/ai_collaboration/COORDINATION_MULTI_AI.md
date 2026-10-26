# Multi-AI coordination on one repository

**Date:** 2026-10-23
**Audience:** Project owner + assistants (including Grok and Z.ai)

## Is conflict inevitable?

No — if branch and file-ownership rules are followed. Conflict appears when two agents rewrite the **same files on the same branch** without coordination.

## Minimum rules

1. **Each agent works on an independent branch** (example: `feat/m2-smart-money-offline` for this Grok track; a separate branch for Z.ai).
2. **One PR per topic**; merge only by owner (or CI) after review.
3. **Before large work:** log a record under `docs/ai_collaboration/` with id, file scope, and status.
4. **Temporary file ownership:** if Z.ai is editing `bootstrap.py`, the other agent must not overwrite it until merge or explicit handoff.
5. **Forbidden:** force-push to `main`; claiming ONLINE_VERIFIED without shared evidence in the matrix.
6. **Semantic conflict:** do not ship two parallel `smart_money` analyzers or two providers registered under the same driver name.

## Suggested split (owner may change)

| Area | Suggested owner | Grok status (this conversation) |
|------|-----------------|----------------------------------|
| TSETMC OHLCV / market-watch mapping | Grok / existing | Partial patch + evidence |
| smart_money model + mock + ShareChangeAnalyzer | Grok | branch `feat/m2-smart-money-offline` |
| daily ingest skeleton | Grok | configs + operations |
| pytse-client mapping | Grok | this docs set |
| UI / Lovable / frontend | Z.ai if that is their track | architecture review discussed earlier |
| Live Codal provider | open / Z.ai or later | placeholder |
| Phase-0 real SOAP samples from Iran IP | **Human + whichever AI logs samples** | requires local Iran run |

## If conflict happens

1. Keep PRs open; do not merge until one side rebases.
2. Owner decides conflicting files (ours/theirs or manual merge).
3. Record outcome in an AI work record (TEST/ADOPT).

## Practical advice right now

- Owner: tell Z.ai which branch and paths they own.
- Both AIs: coordinate before rewriting `bootstrap.py`, `scoring_engine.py`, `providers/base.py`.
- Docs (matrix, CR, mapping) conflict less if appended rather than fully rewritten in parallel.
