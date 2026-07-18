# GHBS Trading TASI — Remaining Work Acceleration Plan

**Date:** 2026-07-18
**Baseline:** main @ 5a4972e (phase-7a-approved)
**Approach change:** Micro-phases (6U…7A) are replaced by larger **Release Trains**, each shipping a complete functional area with tests, docs, verification checklist, and rollback checklist. VPS review still gates each train before merge/tag.

---

## Current State Audit (from repo)

### Backend (FastAPI, `backend/`)
- **Complete and safe:** auth (JWT), safety matrix, secret-status (masked), production DB read-only gate, Telegram readiness + dry-run preview + five-gate manual test-send (Phase 7A), provider readiness, market-data smoke/coverage scaffolding (locked), live analyze/scout preview (locked), dry-run alert scheduler (locked), audit + alert event tables.
- **API surface:** auth, system, dashboard, account, positions, performance, setups, history, audit, analyze, scout, trades, risk, action-plan, journal, integrations, alerts, scheduler, market-data, live-preview.
- **Engine:** `tasi_engine_v7_2_1.py` and core strategy modules (classifier, regime, sizes, chandelier, executor, universe) are **frozen** — no train may modify them.

### Frontend (React + Vite, `src/`)
- Pages: Login, Layout, Pages (hub), Analyze, Scout, ActionPlan, Journal, MarketData, AlertCenter.
- AlertCenter has composer/log/scheduler panels but **no visibility** into the Phase 7A gate model or Telegram readiness.

### Known gaps / debt
- 12 async tests (test_core, test_phase6u) fail to run — `pytest-asyncio` missing from CI env (pre-existing; tests unchanged).
- 3 test files (test_api, test_api_v2b, test_live_preview) have import-time errors in the sandbox environment (pre-existing).
- Legacy `WEBAPP_TELEGRAM_*` env names coexist with canonical `TELEGRAM_*` names in alerts/scheduler/integrations endpoints.
- No DB migration framework (schema created via `CREATE TABLE IF NOT EXISTS`).
- Frontend has no view of safety matrix / gates.

---

## Release Trains

### Train A — Alerts & Telegram Completion *(this branch)*
Scope: everything needed for a safe, admin-driven Telegram alert capability short of any automatic sending.
- Alert template registry (backend, single source of truth; UI consumes it).
- File-based alert/attempt audit layer (JSONL) — no DB migration needed, records locked and allowed attempts with masked data only.
- Unified Telegram status endpoint: readiness + gates + blocked reasons + last attempt.
- AlertCenter UI: readiness panel, gate status, blocked reasons, flags, last dry-run/test-send attempt.
- All sending stays locked by default; scheduler untouched.

### Train B — Test Infrastructure & CI Hardening
- Add `pytest-asyncio` to requirements; repair the 12 skipped async tests and the 3 import-error test files.
- Unify legacy `WEBAPP_TELEGRAM_*` env handling behind `backend/core/secrets.py` accessors.
- Add a repeatable secret-scan script (`scripts/secret_scan.py`) and wire it into a pre-commit/CI checklist.
- GitHub Actions workflow: backend tests + frontend build + secret scan on every PR.

### Train C — Market Data Enablement (gated)
- Promote provider readiness → controlled read-only live quotes behind the existing gate flags.
- Provider fallback chain (yfinance → twelvedata) with per-provider health status in the UI.
- Coverage scan runbook for the TASI universe.

### Train D — Live Preview & Scout Enablement (gated)
- Controlled enablement procedure for live analyze/scout previews on the VPS (read-only, test DB).
- UI surfacing of preview freshness, provider used, and bar sufficiency.

### Train E — Scheduler & Automated Alerts (requires explicit approval)
- Dry-run scheduler hardening; then (approval-gated) real scheduled alert delivery reusing the Train A template registry and five-gate model extended with a scheduler-specific gate.

### Train F — Production Readiness Review
- Read-only production ledger gate exercise, ops runbook consolidation, backup/restore procedure, final security pass.

**Ordering rationale:** A unblocks user-visible value with zero new risk; B removes the recurring test friction that slows every later train; C/D convert already-scaffolded locked features into usable gated ones; E and F are approval-gated by nature.

---

## Standing Constraints (all trains)

1. Strategy logic frozen (engine + classifier/regime/sizing/chandelier/executor/universe).
2. Default state SAFE; every new capability ships locked.
3. No production DB writes; read-only gate only, and only in Train F.
4. No public exposure; Tailscale-only access.
5. No secrets printed, logged, committed, or included in docs.
6. Every train: focused tests + full backend tests + frontend build + secret scan + negative tests before push.
7. No merge to main and no tag without VPS review sign-off.
