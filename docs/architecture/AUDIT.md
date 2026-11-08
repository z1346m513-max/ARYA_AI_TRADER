# ARYA AI TRADER — Project Audit Report (PHASE 1)

Date: 2026-08-09
Auditor: Lovable engineering agent
Scope: full repository inspection prior to any refactor.

---

## 1. What this project actually is

| Aspect | Reality |
| --- | --- |
| Language | TypeScript (no Python anywhere) |
| Runtime | React 19 + TanStack Start v1 (SSR), Vite 8 |
| Styling | Tailwind CSS v4 via `src/styles.css` (@theme tokens) |
| UI kit | shadcn/ui (52 components, unused except a few) |
| Charts | recharts 2.15 |
| Backend | none — no Lovable Cloud, no database, no auth, no server functions |
| Tests | none — no test runner installed |
| Build target | Cloudflare Worker (edge), not a desktop process |
| Package manager | bun (`bun.lock`, `bunfig.toml`) |

There is **no `pyproject.toml`, no `requirements.txt`, no `src/arya/` package, no `configs/`, no `tests/`, no `installer/`, no `docs/`** (this file is the first). The target tree in the specification describes a **Python desktop application**. The repository is a **web application**. This is the single most important finding and is addressed in section 6.

---

## 2. Directory tree (actual)

```text
src/
├── components/
│   ├── arya/            8 presentational components (982 LOC total)
│   │   ├── TopBar.tsx        71   symbol header + timeframe chips (static)
│   │   ├── Sidebar.tsx       69   11 nav items, local useState, NO routing
│   │   ├── ChartPanel.tsx   129   chart container + tabs
│   │   ├── CandleChart.tsx  118   recharts candle/volume render
│   │   ├── ScorePanel.tsx    68   hard-coded score bars
│   │   ├── AiPanel.tsx       74   static "AI recommendation" text
│   │   ├── RightRail.tsx     84   news / codal / alerts placeholders
│   │   └── Architecture.tsx  94   marketing diagram of the pipeline
│   └── ui/              shadcn primitives (untouched)
├── hooks/use-mobile.tsx
├── lib/
│   ├── arya-data.ts    210   seeded mock OHLCV generator + static objects
│   ├── error-capture.ts / error-page.ts / lovable-error-reporting.ts  (platform)
│   └── utils.ts
├── routes/
│   ├── __root.tsx      root shell, HeadContent, providers
│   └── index.tsx       the ONLY page — whole dashboard on one screen
├── router.tsx, server.ts, start.ts, styles.css, routeTree.gen.ts
```

---

## 3. Status classification

### EXISTING (works today)
- Dark financial-terminal visual language, RTL Persian layout, semantic color tokens in `styles.css`.
- Deterministic mock OHLCV generator (`generateSeries`) — seeded per ticker, reproducible.
- Candlestick + volume + MA20/MA50 rendering via recharts.
- Responsive 4-column dashboard shell (chart / score / AI / rail).
- Correct SEO head on `/`.
- Clean TanStack Start bootstrap; build and typecheck pass.

### MISSING (specification vs. reality — everything below is absent)
- Configuration engine (`configs/*.yaml`), user-editable indicator parameters.
- Provider abstraction (`BaseProvider`, Iran/Crypto/Forex/News/Codal/Macro).
- Indicator engine — **zero** of the 33 required indicators exist as reusable units. RSI/MA are inlined inside the mock generator.
- Pattern recognition (candlestick + chart patterns).
- Smart Money / market-structure engine (BOS, CHOCH, OB, FVG, liquidity).
- Fundamental engine, Codal engine, News/sentiment engine.
- Scoring engine, weighting model, normalization/validation.
- AI decision engine (no AI wired at all; the "AI panel" is static prose).
- Risk engine, backtester, optimizer.
- Scanner, watchlist, portfolio, stock comparison, alerts, reports.
- Scheduler / auto-refresh.
- Persistence of any kind.
- Data-integrity metadata (source / timestamp / status / quality).
- Any test, any documentation, any CI.

### BROKEN / MISLEADING (must fix early — data-integrity rule #28)
1. `AiPanel.tsx` presents a confident BUY-style recommendation with entry/SL/TP that is **hand-written text**, not computed. Violates rule 38.
2. `ScorePanel.tsx` score numbers are literals with no engine behind them.
3. `RightRail.tsx` news and Codal items are invented headlines shown as if real.
4. Nowhere is `DATA_STATUS = DEMO` displayed. Everything looks live.
5. `TopBar` timeframe chips and `Sidebar` items are decorative — clicking changes nothing (Sidebar sets local state only; there is one route).

### DUPLICATED
- None significant. Mock-data shapes are defined once in `arya-data.ts`.

### NEEDS REFACTOR
- `arya-data.ts` mixes provider simulation + indicator math + static content. Must split into `providers/mock`, `technical/*`, and view-model layers.
- Sidebar navigation must become real TanStack routes before any page work.
- Components read data directly; needs a domain layer + query layer between them.

### READY (usable foundation, keep)
- Design tokens and panel styling.
- recharts chart primitives.
- shadcn component library.
- TanStack Start routing/SSR bootstrap.

---

## 4. Dependency assessment

Present and sufficient for phases 2–8: `zod` (config validation), `@tanstack/react-query` (caching/scheduling), `recharts`, `date-fns`, `react-hook-form`.

Not present, will be required later: a test runner (`vitest`), a YAML parser if we keep `.yaml` configs, a backend (Lovable Cloud) for persistence, and an AI gateway client for the decision engine.

Notably: `child_process`, native binaries, `sharp`, and PyInstaller-class tooling are **unavailable** — the server runs on Cloudflare Workers.

---

## 5. Risk register

| # | Risk | Severity | Mitigation |
| --- | --- | --- | --- |
| R1 | Spec targets Python/Windows; repo is a web app | Critical | Section 6 decision required |
| R2 | Mock data displayed as real | High | Ship data-integrity layer in Phase 2, before any new feature |
| R3 | Building 33 indicators + 8 engines without tests | High | Install vitest in Phase 2; no engine merges without unit tests |
| R4 | Single-route app cannot host 11 planned sections | High | Route scaffold in Phase 2 |
| R5 | Over-fitting in backtest/optimizer | Medium | Walk-forward + out-of-sample enforced by design in Phase 12 |
| R6 | Iran market (TSETMC/Codal) has no official public API | Medium | Provider interface first; real adapter behind a feature flag |

---

## 6. Architecture decision required — Python desktop vs. TypeScript web

The specification's target tree (`src/arya/**`, `pyproject.toml`, `ARYA_AI_TRADER_Setup.exe`) cannot be built in this repository. This environment builds and hosts React/TanStack web applications; it cannot compile a Python distribution or produce a Windows installer.

Two coherent paths:

**Path A — Web-native ARYA (recommended).** Keep TypeScript. Implement the *same* modular architecture with identical module boundaries and identical responsibilities, mapped onto the web stack:

```text
spec module            →  this repo
src/arya/providers/    →  src/arya/providers/
src/arya/technical/    →  src/arya/technical/
src/arya/analysis/     →  src/arya/analysis/
src/arya/scoring/      →  src/arya/scoring/
src/arya/smart_money/  →  src/arya/smart-money/
src/arya/risk/         →  src/arya/risk/
src/arya/backtest/     →  src/arya/backtest/
configs/*.yaml         →  src/arya/config/*.ts (zod-validated, YAML-shaped)
storage/               →  Lovable Cloud (Postgres) + query cache
ui/ + dashboard/       →  src/routes/* + src/components/arya/*
tests/                 →  vitest, colocated + tests/
installer/             →  deferred; desktop shell (Tauri/Electron) is a
                          separate repo consuming the same core
```
Every engine is written as pure, framework-free TypeScript in `src/arya/**` so it stays portable, testable in Node, and reusable by a future desktop shell.

**Path B — Rewrite in Python.** Matches the spec literally, but this repository and its preview cannot run or ship it; you would lose the existing UI and get no runnable product here.

Recommendation: **Path A**. It preserves every architectural principle in the specification (modularity, configurability, weighting, data integrity, testing, staged delivery) while producing a product that actually runs, and it leaves the Windows packaging option open through a desktop shell over the same core.

---

## 7. Proposed Phase 2 scope (pending decision)

1. Create `src/arya/**` core skeleton with real, non-placeholder module boundaries.
2. Data-integrity layer: `DataEnvelope<T>` carrying `source`, `timestamp`, `status` (`LIVE | DEMO | UNAVAILABLE | STALE`), `quality`; a visible `DEMO` badge wherever mock data reaches the screen.
3. `vitest` installed; first unit tests covering the envelope and the config validator.
4. Route scaffold for the 11 sidebar destinations; Sidebar switched to real `<Link>` navigation.
5. `src/arya/config/` with zod schemas for indicators, weights, timeframes, scheduler, risk — defaults matching the specification, all user-overridable.

No feature is considered complete without: code, tests, integration, UI (where applicable), configuration, error handling, and documentation.

---

## 8. Phase 1 report

```text
PHASE:   1 — Project Audit
STATUS:  COMPLETE

Completed:
- Full directory, dependency and runtime inspection
- Classification: EXISTING / MISSING / BROKEN / DUPLICATED / NEEDS REFACTOR / READY
- Risk register (6 items)
- Architecture gap analysis + migration options

Files Created:
- docs/architecture/AUDIT.md

Files Modified:
- none (no code touched, per instruction 2)

Tests:
- none exist yet (test runner absent)

Known Issues:
- R1 blocks Phase 2: Python/Windows target vs. web runtime
- R2 data-integrity violations live in the current UI

Next Step:
- Owner decision on Path A vs Path B, then Phase 2
```
