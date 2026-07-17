# Phase 6I: Release Candidate Checklist & Final Safety Assertions

## Release Version
**GHBS Trading Web Sandbox - Version 1.0.0-rc.1**

## Prerequisites
- [x] Phase 6H (Safety Regression Release Hardening) passed natively.
- [x] All test suites pass without regressions (`pytest`).
- [x] React frontend builds successfully (`npm run build`).

## 1. Safety Matrix Guard Baseline 
- [x] `ALLOW_PRODUCTION_DB` inherently defaults to `false` system-wide.
- [x] `DB_PATH` sets context to `tasi_ledger_test.db` globally unless explicitly overridden securely.
- [x] A runtime protection (`is_db_blocked()`) completely disables mutation pathways dynamically if `ALLOW_PRODUCTION_DB=false` and `DB_PATH=tasi_ledger.db` configurations interact together unexpectedly. Safety endpoints return clean generic 503 statuses instead of breaking entirely.
- [x] Live Preview executions (Scout, Analyze) correctly enforce `audit-only` routes to `live_preview_runs` keeping positions and transactions completely protected. Log insertions never persist beyond specific analysis schemas.

## 2. API Key Protections
- [x] `.env.example` verified: purely includes structural placeholder names. No active credentials exist.
- [x] Hardcoded tokens verified: Application logic explicitly depends entirely on standard OS environment injection.
- [x] Settings UI explicitly masks API tokens utilizing partial reveal logic defensively keeping original outputs strictly private.
- [x] Web Telegram API tokens isolated strictly. Unapproved message paths default out correctly via `dry_run` structures.

## 3. Configuration Default Alignments
The application environment starts safely disabled ensuring maximum security:
- [x] `ENABLE_MARKET_DATA_SMOKE_TESTS=false`
- [x] `ENABLE_PROVIDER_COVERAGE_SCAN=false`
- [x] `ENABLE_LIVE_ANALYZE_PREVIEW=false`
- [x] `ENABLE_LIVE_SCOUT_PREVIEW=false`
- [x] `ENABLE_ALERT_SCHEDULER=false`
- [x] `ALERT_SCHEDULER_DRY_RUN_ONLY=true`

## 4. UI Visibility Alignments
- [x] Pre-Auth `Safety Matrix` visual indicators function correctly when the database backend responds via `HTTP 503` `DB blocked` status preventing visual silence on degraded execution branches.
- [x] Post-Auth setting matrices successfully match backend toggles transparently. Toggle options purely drive UI layouts rendering operations safe and descriptive.

## 5. Algorithmic Freezes
- [x] Strategy Engine is fully locked.
- [x] Target and threshold logics strictly operate utilizing `Phase 6A` original states.
- [x] `ChandelierEngine`, `SizingEngine`, and `classify_setup` remain unmodified.

## Certification
**This candidate has been formally approved as a Safe Baseline Sandbox release.** Deployments made out of this snapshot pose negligible risk to real resources when default constraints are logically respected.
