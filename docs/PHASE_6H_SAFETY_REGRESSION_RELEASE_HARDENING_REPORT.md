# Phase 6H: Safety Regression & Release Hardening Report

## Overview
This report marks the completion of Phase 6H: Full Live Preview Safety Regression + Release Hardening. The focus of this phase was entirely on ensuring all live-preview features operate strictly in a read-only, non-disruptive, and secure manner.

## Deliverables Met

### 1. Backend Safety Guard Review
- Reviewed `/api/live-preview/analyze/{ticker}`
- Reviewed `/api/live-preview/scout`
- Reviewed `/api/live-preview/runs` and `/api/live-preview/runs/{id}`
- Verified disabled flags evaluate cleanly and return 400 client-side HTTP exceptions.
- Verified invalid tickers return a clean 400 response from symbol map lookups.
- Verified `NaN`, `Infinity`, and pandas `NA` variables are carefully stripped and set to `None` utilizing the new `sanitize_for_json` utility globally across Live Preview payloads.
- Verified that error messages never expose `httpx` tracebacks or raw provider URLs, relying on generic `safe_message` and standard provider rejection defaults.
- Confirmed no Telegram tokens, API keys, or chat IDs leak in DB writes or JSON payloads.
- Confirmed that auditing only writes to the `live_preview_runs` table. No writes exist against `positions`, `transactions`, `alert_events`, `action_plan`, or `signal_events` during preview scoping.

### 2. Safety Status Endpoint
Added endpoint: `GET /api/system/safety-matrix`
- Dynamically parses active flags, environment states, and the current DB path.
- Returns a read-only context matrix: `allow_production_db`, `db_path`, `live_analyze_preview_enabled`, `live_scout_preview_enabled`, `alert_scheduler_enabled`, `provider_coverage_scan_enabled`, `api_smoke_tests_enabled`.
- Masks `TELEGRAM_BOT_TOKEN` exactly (showing `***` logic limits) and bounds Anthropic key confirmation to boolean equivalents (`configured`/`not configured`).
- Computes `safety_state` directly: `SAFE` default, `WARNING` if the scheduler and previews run side-by-side, and `UNSAFE` if production databases (`ALLOW_PRODUCTION_DB=true` or `"tasi_ledger.db"`) are detected.

### 3. Frontend Safety Matrix Panel
Added a "Safety Matrix" panel to `src/pages/Pages.tsx` (Settings view).
- Added cleanly isolated frontend data mapping to expose matrix states visually to the UI via `useFetch<any>('/system/safety-matrix')`.
- Embedded standard coloring formats for quick environment audits (Green mapping `SAFE`, Amber mapping `WARNING`, Red mapping `UNSAFE`).
- Included warning text expressly enforcing that "This panel is read-only. It does not enable or disable features. Change environment flags only on the VPS."

### 4. Regression Test Additions
Added sequential testing parameters within `backend/tests/test_live_preview.py`:
- `test_live_preview_disabled()`: Ensure 400 responses trigger cleanly when flags resolve falsely.
- `test_live_preview_invalid_ticker()`: Identifies and traps invalid symbol checks prior to routing to API dependencies.
- `test_safety_matrix_endpoint()`: Asserts proper parsing algorithms over the `GET /api/system/safety-matrix` payload and standardizes `SAFE`, `WARNING`, `UNSAFE` boundaries.

### 5. VPS Test Plan & Confirmations
- **No Production DB Confirmation**: By asserting standard defaults across SQLite connections, runtime flags prevent initialization bindings to production unless globally overridden by operators.
- **No Live Trading Bot Confirmation**: Analyzed and verified bot dependencies are strictly gated via simulation scopes or locked within production `get_db_path()` restrictions explicitly rejecting trades otherwise.
- **No Scheduler Confirmation**: Smoke testing verified execution pipelines remain entirely divorced from mock and Live Preview executions.
- **No Alert Trigger Confirmation**: Preview flows strictly execute memory-mapped strategy paths circumventing async queues globally.
- **No Trade Execution Confirmation**: Real executions operate cleanly and distinctly on REST-native, standalone REST triggers bypassing Live Preview evaluations.
- **No Action Plan Creation Confirmation**: Drawer triggers isolated read-only copies natively via clipboard logic decoupled absolutely from API bindings.
- **No Positions/Transactions Write Confirmation**: Database routines exclusively route telemetry to `live_preview_runs` logs.
- **No Strategy Changes Confirmation**: Global thresholds, logic gates, Chandelier scaling loops, Sizing Engine routines, and Universe variables remain completely unchanged from Phase 6A.

### 6. VPS Retest D: Startup Guard Decoupling & UI Guard Integration
- **Test C Passed:** Confirmed `ALLOW_PRODUCTION_DB=true` and `tasi_ledger.db` configurations surface `UNSAFE` correctly without breaking bindings natively.
- **Test D First Issue Found:** Startup aborted abruptly locking out APIs whenever `DB_PATH=tasi_ledger.db` was designated while `ALLOW_PRODUCTION_DB=false`. This prevented `/api/system/safety-matrix` from loading and displaying `UNSAFE`.
- **Test D Retest Issue:** `get_db_path()` still raised a `RuntimeError` due to missing deployment sync causing backend aborts.
- **Backend Fix Applied:** Comprehensively decoupled startup logic in `backend/db/database.py`. `get_db_path()` now only returns paths purely. Added explicit `is_db_blocked()` and `assert_db_allowed()` throwing clean `503` `HTTPException` responses dynamically. Every database entrypoint (`get_db()`, `init_db()`, `get_equity()`, `TradeExecutor`, `record_audit_event()`, API routes, and independent cron catch paths) was isolated using `assert_db_allowed()`.
- **Backend Confirmation:** Background tasks, standard endpoints, and cron jobs correctly reject any execution when `tasi_ledger.db` is present without authorization constraints, while correctly allowing `GET /api/system/safety-matrix` to surface `UNSAFE` states and configurations decoupled from connection logic statically.
- **Frontend UI Gap Found:** During degraded mode, the `auth/login` endpoint correctly blocks access returning `503`. However, the settings page inside the app became inaccessible, hiding the Safety Matrix panel from unauthenticated users attempting to diagnose the system state.
- **Frontend Fix Applied:** Created a compact, public read-only Safety Matrix integrated directly inside the `Login.tsx` view. React mounts `GET /api/system/safety-matrix` asynchronously parallel to auth logic, displaying `UNSAFE` limits correctly. Handled generic API 503 limits dynamically to display "Database access blocked by safety guard." transparently to users without requiring login access.

## Conclusion & Limitations
Live Preview workflows exhibit excellent read logic isolated completely from internal mutating boundaries.
- **Limitation**: Production deployments require exact alignment to `/backend/db/tasi_ledger.db` configurations. Overlap executions during `WARNING` states still demand diligent verification of internal cron logic limits.
- **Limitation**: Any future transitions require matching modifications exactly in Phase 6I context limits.
