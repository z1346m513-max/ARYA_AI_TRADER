# ARYA AI TRADER — Architecture Standard & Multi-Agent Work Orders

**Date:** 2026-10-31  
**Status:** Proposed for owner approval; not yet merged into `main`  
**Repository:** `z1346m513-max/ARYA_AI_TRADER`

> This document supplements `AGENTS.md`, `docs/governance/PLATFORM_CONSTITUTION.md`, `STARTUP_CHECKLIST.md`, `CHANGE_LEDGER.md`, and the existing source registry. If any conflict exists, the Constitution and owner decision take precedence.

## 1. Owner decision and operating principles

1. `main` is the stable reference. No direct commits to `main`; every change uses a dedicated branch and Pull Request.
2. The project owner alone accepts architecture changes, shared contracts, scope changes, merges, and activation of paper/live execution.
3. No API, field, endpoint, rate limit, legal permission, or market-data behavior may be inferred from an AI answer. Evidence must be traceable to a primary source or a reproducible test.
4. Research workstream does not modify application code. Coding workstreams do not independently investigate or redefine external-source contracts.
5. A Recommendation is analytical advice, not an order authorization. Live trading remains disabled by default.
6. AI agents may research, implement within a bounded scope, test, and review. They may not silently change product policy, risk policy, shared contracts, or another agent's work.
7. A model response is not evidence. Every factual claim about a source/API must include source URL, access date, exact observation, evidence artifact, and verification status.

## 2. Architecture standard

### 2.1 Analysis and recommendation path (current target)

`Analyst/CLI → Application Workflow → Provider Registry → Market Data Gateway → Normalizer/Validation → OHLCV Store → Indicator Engine → Technical/Fundamental Analysis + Filters + Strategy → Scoring → Decision → Independent Risk Manager → Recommendation Builder → AnalysisResult → CLI/Dashboard`

- Providers implement stable interfaces; external API details stay inside adapters.
- Normalization and validation occur before analysis.
- Data carries source, timestamp, freshness, quality, and provenance.
- Indicators and strategies are registered through explicit contracts and versioned configuration.
- Scoring exposes component scores, weights, missing inputs, and total calculation.
- Decision output is structured and versioned.
- Risk Manager is an independent gate. It must not depend on, or take instructions from, an AI/LLM decision component.
- Recommendation includes decision, risk result, data quality, warnings, and provenance.
- Dashboard displays results; it does not create decisions or orders.

### 2.2 Future execution path — not assumed implemented

`Recommendation candidate → Trade Validator → Portfolio Manager → Position Sizer → Independent Risk Gate + Kill Switch → Order Service (idempotent) → Broker Adapter → Order Tracker → Reconciliation`

This path is future scope unless proven by code, tests, and an accepted Change Record. No Analyzer, Strategy, LLM, CLI, or Dashboard may send orders directly. Paper and live environments require separate credentials, endpoints, policies, and safeguards. Live mode requires explicit owner authorization and must remain off by default.

### 2.3 Required data semantics

All shared contracts must define:
- `schema_version`, `source`, timezone-aware `timestamp`, `data_quality`, and `provenance`.
- `missing`, `unknown`, `partial`, `stale`, and `usable` as distinct states with documented consumer behavior.
- Correlation identifiers for cross-module tracing; idempotency keys for operations that can be repeated.
- Explicit units, currency, price scale, volume units, timezone, trading calendar, symbol mapping, and adjustment policy where relevant.

Unknown values must not be silently converted to zero. Partial or stale inputs must not produce a fully approved trade recommendation. Invalid OHLCV must fail closed.

### 2.4 Implementation status and evidence vocabulary

Every material component, deliverable, and acceptance criterion must have an explicit implementation status. Use only these values:

- `IMPLEMENTED`: implemented in the repository and supported by reviewable evidence and the applicable test/validation results.
- `PARTIALLY_IMPLEMENTED`: some defined parts are implemented, while the remaining parts are explicitly listed.
- `PROPOSED`: designed or recommended, but not implemented in the repository.
- `BLOCKED`: work cannot proceed because of a documented dependency, missing permission, evidence gap, or technical/legal blocker.

`UNVERIFIED` is **not** an implementation status. It is an evidence qualifier used when a claim, source, behavior, connection, or test result has not been independently verified. It may accompany any implementation status where appropriate (for example, `PARTIALLY_IMPLEMENTED; evidence: UNVERIFIED`). Do not use `UNVERIFIED` as a substitute for stating whether a component is implemented.

Rules:
1. Assign status per component; do not infer the status of an entire subsystem from the presence of a file or class.
2. For `IMPLEMENTED`, cite the relevant paths/commit and provide the exact validation evidence. If required tests were not run, state `NOT RUN` and explain the limitation; do not imply full verification.
3. For `PARTIALLY_IMPLEMENTED`, list completed and outstanding parts separately.
4. For `PROPOSED`, distinguish design/documentation from runtime implementation.
5. For `BLOCKED`, state the blocker, evidence needed, responsible owner, and next decision.
6. Never describe offline tests as proof of live connectivity, production readiness, trading performance, or profitability.

## 3. Workstream R — External source research and online connectivity

**Recommended coordinator:** Perplexity  
**Browser/API verification:** Manus  
**Independent evidence challenge:** Grok  
**Technical research support:** ChatGPT (architecture, evidence review, acceptance)  
**Important:** These are role recommendations, not claims of a permanent benchmark ranking. Use the strongest available model/version and record the model/version and date.

### 3.1 Mission

Inventory, verify, document, and test (in a read-only/safe manner) the external sources required by ARYA, initially:
1. TSETMC — market instruments, prices, OHLCV, market status, trade/volume data, and any public client-type/investor-flow data.
2. Codal — issuer disclosures, financial statements, board decisions, capital changes, earnings forecasts, and other official filings.
3. Official fund/ETF sources — fund NAV, holdings, portfolio composition, unit counts, and official reports.
4. Official market/regulatory sources — exchange notices, market calendars, instrument metadata, corporate actions, and suspensions.
5. Official macroeconomic sources — central bank, statistics authority, ministry, and other primary sources only where they materially affect supported analyses.
6. News sources — only after source identity, publication time, reuse conditions, and a verifiable retrieval method are documented.

Do not expand to unrelated websites merely to increase source count. Prioritize official primary sources and the specific ARYA data requirements.

### 3.2 Source research procedure

For each source, produce a separate record containing:
- Source name, official domain, organization/operator, purpose, and official documentation URL.
- Exact data categories and fields available; field definitions, units, currency, scale, timezone, and symbol/issuer identifiers.
- Access method: documented API, public web page, downloadable file, authenticated API, or browser-only workflow.
- Endpoint/method/query parameters and sample request/response, with secrets and personal data removed.
- Authentication, API key requirements, cookies/session dependence, rate limits, pagination, date ranges, and known quotas.
- Terms of use, robots/access restrictions, copyright/licensing, redistribution and storage permissions. If unclear: `LEGAL_REVIEW_REQUIRED`.
- Data freshness, historical depth, update cadence, correction/revision behavior, missing-data behavior, and known gaps.
- Online connectivity test result from the actual target environment: timestamp, DNS/TLS/HTTP outcome, latency, response code, and sanitized response sample.
- Reliability risks: schema drift, anti-bot behavior, throttling, unstable unofficial endpoints, non-exact symbol matching, stale cache, and outage behavior.
- Verification status: `VERIFIED`, `PARTIAL`, `UNVERIFIED`, `BLOCKED`, or `REJECTED`.
- Recommendation: `ADOPT`, `ADOPT_WITH_LIMITS`, `SPIKE_REQUIRED`, or `DO_NOT_USE`, with reasons.

### 3.3 Verification rules

- First choice: official API documentation and official downloadable datasets.
- An endpoint observed in browser developer tools is not automatically a supported API. Label undocumented endpoints `UNOFFICIAL/UNVERIFIED` until legal and technical review.
- A successful DNS lookup does not prove the endpoint works. HTTP 200 does not prove data correctness. A successful one-time request does not prove reliability.
- Capture at least one sanitized real response and validate it against a documented schema. If live access is blocked, state exactly what failed; do not infer the service is down.
- Test symbol resolution with exact-match cases and ambiguous tickers. Never silently fall back to the first search result.
- Check date attribution using explicit source timestamps/market dates. Matching volume alone is not proof that a snapshot belongs to a historical date.
- Record whether a value is raw, adjusted, delayed, end-of-day, intraday, indicative, or official.
- No production code, provider config, credentials, scraping jobs, or scheduled fetchers are changed by Workstream R.

### 3.4 Deliverables

Create evidence-backed documents under `docs/research/sources/` (or the existing approved source-doc location):
1. `SOURCE_INVENTORY.md` — source matrix and priority.
2. One source dossier per provider, e.g. `TSETMC_SOURCE_DOSSIER.md`, `CODAL_SOURCE_DOSSIER.md`.
3. `CONNECTIVITY_TESTS.md` — reproducible commands, environment, timestamps, sanitized results.
4. `DATA_DICTIONARY.md` — canonical field mapping, units, types, timestamps, symbol identifiers, null semantics.
5. `SOURCE_ADOPTION_DECISIONS.md` — accepted/rejected/blocked sources and rationale.
6. Proposed provider contracts and sample fixtures, clearly marked as proposals and not merged into runtime code.
7. One Change Record for each meaningful research milestone, with evidence links and a Ledger entry.

**Acceptance:** No source is approved for implementation until official/primary evidence, field semantics, legal/access status, sample payload, and a reproducible connectivity or explicit blocker report are reviewed by the owner.

## 4. Workstream C1 — Provider and ingestion implementation

**Recommended primary coding assistant:** Claude (coding agent/IDE mode).  
**Scope:** provider/ingestion boundary only, after Workstream R source dossier and owner acceptance.

Allowed paths (confirm actual repo layout before editing):
- `src/arya/providers/**`
- `src/arya/data/**` or the existing approved ingestion package
- `src/arya/storage/**` only for provider-ingestion persistence changes explicitly assigned
- `configs/providers.yaml` only for approved provider configuration
- Provider-specific tests and fixtures
- Provider technical documentation/Change Records assigned to C1

Tasks:
1. Inspect existing provider contracts and implement adapters only against owner-approved source dossiers.
2. Add strict symbol/issuer resolution; reject ambiguous or non-exact matches unless an explicit mapping is configured.
3. Normalize timestamps, units, currency, price scales, volume, trading calendar, corporate-action adjustments, and null semantics.
4. Implement timeout, bounded retry/backoff, rate limiting, caching/freshness policy, and sanitized error reporting.
5. Preserve raw response evidence or stable fixture hashes where policy permits; never store secrets.
6. Add deterministic offline tests with sanitized fixtures. Keep live smoke tests separate and opt-in.
7. Do not change analyzer, scoring, risk, recommendation, decision, UI, or order execution logic.
8. Do not invent a source field or endpoint if the research dossier is incomplete; stop and request evidence.

**C1 acceptance:** contract tests, parser tests, negative/ambiguous symbol tests, stale/missing/error tests, offline full suite, and separately reported live smoke test. No claim of online readiness without target-environment evidence.

## 5. Workstream C2 — Analysis, scoring, risk, and recommendation

**Recommended primary coding assistant:** DeepSeek (implementation) or Claude if one coding seat is available.  
**Independent reviewer:** Z.ai or Grok for design challenge; reviewer must not edit the same files in parallel.  
**Scope:** analysis and decision logic only. C2 must use existing provider contracts and Mock/fixture data; it must not access external sites or change provider adapters.

Allowed paths (confirm actual repo layout before editing):
- `src/arya/analysis/**`
- `src/arya/technical/**`
- `src/arya/ai/reasoning/**`
- `src/arya/risk/**`
- `src/arya/models/analysis_result.py` only when specifically approved
- Related tests, fixtures, and analysis documentation

Tasks:
1. Audit analyzers and their inputs/outputs; document gaps before changing behavior.
2. Ensure scoring is deterministic, versioned, explainable, and exposes component-level contributions and missing inputs.
3. Ensure incomplete/stale/invalid evidence cannot be silently promoted to a high-confidence signal.
4. Keep Risk Manager independent from AI/LLM decision logic; risk may reject a decision.
5. Make Recommendation clearly advisory and include quality, provenance, warnings, and risk assessment.
6. Add boundary, regression, property, replay, and integration tests using Mock/fixtures.
7. Do not create or send orders; do not change Provider/API contracts; do not add external network calls.
8. Do not retune weights or trading thresholds without a separate owner-approved decision record.

**C2 acceptance:** deterministic fixture tests, missing/partial/stale cases, score explainability tests, risk rejection tests, recommendation schema tests, and no forbidden imports/dependencies.

## 6. Strict non-overlap and sequencing

| Workstream | Owner/model roles | Owns | Must not touch |
|---|---|---|---|
| R — source research | Perplexity lead; Manus verification; Grok challenge | `docs/research/sources/**`, source evidence, connectivity reports | Runtime code, provider configs, credentials |
| C1 — provider/ingestion | Claude primary coder | Provider, normalization, ingestion, provider tests | Analysis/risk/decision/UI |
| C2 — analysis/risk | DeepSeek or Claude (only if C1 is not using it); Z.ai/Grok review | Analysis, technical, scoring, decision, risk, recommendation tests | Provider adapters, source investigation, provider configs |
| Owner/architecture gate | Project owner; ChatGPT assists review | Shared contracts, scope, ADRs, acceptance, merge decisions | Unreviewed implementation |

Sequencing:
1. R inventories sources and submits evidence. No runtime code changes.
2. Owner accepts/rejects each source and freezes the proposed field contract.
3. C1 implements one provider slice at a time against accepted contracts.
4. C2 may work in parallel only on existing Mock/fixture contracts. Shared model/contract changes are frozen; if needed, submit a proposal and wait for owner decision.
5. C1 and C2 each open separate PRs. No agent merges its own work.
6. Integration occurs only after independent review and owner approval.

If only one coding assistant is available, run C1 then C2 sequentially. Do not ask one agent to edit a file while another agent is reviewing/editing that same file.

## 7. Required stage log and Change Record

Every meaningful stage must produce a durable project record before work proceeds.

Use one Change Record per stage under `docs/changes/CR-YYYYMMDD-NNN-<slug>.md`, then add its row to `docs/governance/CHANGE_LEDGER.md`.

Required template:

```markdown
# CR-YYYYMMDD-NNN — <title>

- Record status: PROPOSED | IMPLEMENTED | PARTIALLY_IMPLEMENTED | BLOCKED
- Workstream: R | C1 | C2 | Integration | Governance
- Date/time (include timezone):
- Owner/requestor:
- Responsible agent/person:
- Agent/model name and exact version:
- Repository, branch, base branch, and base commit:
- PR URL/number and commit SHA (or NOT CREATED):
- Objective and scope:
- Components/deliverables and per-component implementation status:
  - <component/path>: IMPLEMENTED | PARTIALLY_IMPLEMENTED | PROPOSED | BLOCKED
- Files changed:
- Files deliberately not changed:
- Dependencies and prerequisite decisions:
- Evidence inventory:
  - Source/document title:
  - URL:
  - Access/retrieval date and time (timezone):
  - Source/data publication or effective date:
  - Trust level (official primary / official secondary / reputable secondary / community / unverified):
  - Exact claim or observation supported:
- Tools, environment, and access used (including whether network/API access was available):
- Implementation summary and decisions/rationale:
- Tests and validation:
  - Exact command:
  - Exact result/output:
  - Status: PASS | FAIL | NOT RUN
  - If NOT RUN/FAIL, reason and impact:
- Connectivity status (NOT APPLICABLE | VERIFIED | PARTIAL | BLOCKED | UNVERIFIED), with timestamp and evidence:
- Security/privacy review:
- Legal/licensing/terms review:
- Suggestions and alternatives:
- Criticisms / unresolved risks:
- Known limitations and unsupported claims:
- Follow-up tasks:
  - Owner:
  - Dependency:
  - Acceptance criterion:
- Reviewer and review date:
- Owner decision and decision date:
```

Status and evidence rules:
- Implementation status values are only `IMPLEMENTED`, `PARTIALLY_IMPLEMENTED`, `PROPOSED`, and `BLOCKED`.
- `UNVERIFIED` is an evidence qualifier, not an implementation status. Apply it to the specific unverified claim/source/behavior.
- A record may be `IMPLEMENTED` while explicitly identifying a separate unverified connectivity claim; do not conflate the two.
- Never claim tests passed unless the exact command was run and its result captured. Use `NOT RUN` when applicable.
- Record evidence URLs and access dates. A model-generated answer without independently reviewable evidence is not a source.
- The PR/commit field must contain the actual reference or the literal `NOT CREATED`.

At the end of each stage, the agent must provide:
1. What was completed — with file paths, per-component status, and commit SHA (or NOT CREATED).
2. What was not completed and why.
3. Evidence used, URLs, access dates, and trust levels.
4. Tools/access used and whether external connectivity was actually tested.
5. Exact test commands and outputs; never report tests not run as passing.
6. Security/legal considerations, suggestions, criticism, risks, and limitations.
7. Follow-up owner, dependencies, acceptance criteria, and questions requiring owner decisions.
8. Next proposed bounded task.

No stage is considered complete until the Change Record and Ledger entry are present in the same PR as the change. Research-only milestones also require records, even if no code changes.

## 8. PR and safety requirements

- Start every session by reading `AGENTS.md`, Constitution, Startup Checklist, latest Change Records/Ledger, relevant ADRs, and source registry.
- Record `git status --short --branch`, current branch, base commit, and untracked files before changes.
- Never delete, reset, clean, overwrite, or stage unrelated/untracked user files.
- One bounded workstream per branch/PR. No shared branch between agents.
- Include exact test commands and results in PR description.
- Unit tests must be offline. Live connectivity tests are separate, explicitly enabled, and sanitized.
- No secrets, tokens, cookies, personal data, or account credentials in repository or logs.
- No scraping or automation that violates source terms, access restrictions, or applicable law.
- No merge, production schedule, or live-trading activation without owner approval.
- If evidence is missing, stop and record `UNVERIFIED/BLOCKED`; do not fill gaps with assumptions.

## 9. Suggested first assignments

### R-01 — Source inventory and Codal/TSETMC connectivity evidence
Perplexity leads source discovery and citations. Manus verifies official pages, observed request flows, and safe read-only connectivity. Grok challenges the evidence and searches for overlooked failure modes. Deliver the source inventory, TSETMC and Codal dossiers, connectivity report, data dictionary draft, and Change Record. No code edits.

### C1-01 — Existing provider contract audit (blocked until R-01 acceptance)
Claude reviews current provider abstractions and produces an implementation plan only. It must not add endpoints or code until source evidence and owner-approved contracts exist.

### C2-01 — Analysis/risk audit using current fixtures
DeepSeek (or Claude if only one coder) audits analysis/scoring/risk/recommendation behavior using existing fixtures. It may add tests only within its assigned paths after the owner approves the exact scope. No provider or network changes.

### Integration gate
After R-01 and the first C1/C2 reports, ChatGPT can compare their evidence, diffs, test outputs, architecture boundaries, and unresolved decisions and return an owner-facing acceptance report. This review does not replace owner approval.

## 10. Assistant role recommendations

| Assistant | Recommended use in this project | Avoid assigning |
|---|---|---|
| Perplexity | Lead source discovery, citations, official documentation cross-references | Final API approval or code changes based only on summaries |
| Manus | Browser-based verification, repeatable navigation, read-only source exploration | Unreviewed scraping, credential handling, production writes |
| Grok | Independent challenge, alternative source discovery, edge-case review | Simultaneous edits to C1/C2 files |
| Claude | Primary coding agent for provider adapters or a bounded coding workstream | Owning source truth without primary evidence |
| DeepSeek | Secondary implementation or test-generation/review for isolated analysis modules | Concurrent edits with Claude in the same scope |
| Z.ai | Independent code review, test-gap review, alternative implementation critique | Changing shared contracts without approval |
| Genspark | Supplementary research discovery and report comparison | Sole evidence source |
| Groq | Fast inference/triage if a suitable model is selected | Assuming hosting/inference speed implies coding correctness |
| Arena | Comparing model outputs on a fixed rubric | Treating preference/votes as factual verification |
| ChatGPT | Architecture coordination, requirements decomposition, evidence audit, PR review, stage acceptance report | Replacing owner approval or source-side live tests |

Model versions and tool capabilities change. At task start, record the exact model/version and available tool access. Choose by measured performance on a small project-specific benchmark (source accuracy, code correctness, test quality, instruction adherence), not brand reputation.

## 11. First acceptance gate

Do not start broad implementation until the following are available:
- Current main commit and repository instructions reviewed.
- Source inventory and official evidence for the first provider(s).
- Explicit access/legal status and online connectivity result or a documented blocker.
- Approved canonical field dictionary and provider contract.
- Separate C1/C2 scopes with path ownership.
- Stage Change Record and acceptance criteria.
- Owner approval of the first bounded implementation tasks.
