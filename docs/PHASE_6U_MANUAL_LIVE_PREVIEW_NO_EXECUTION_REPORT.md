# Phase 6U - Manual Live Preview Enablement, No Execution

## Overview
This phase introduces a strictly controlled manual live preview enablement layer for Analyze and Scout functionalities. It ensures that the user can test the live market data pipelines for specific symbols without triggering any execution logic, database writes, or automated tasks.

## Safety Boundaries Implemented
- **No Execution**: A new `execution_guard.py` acts as a hard stopper to prevent any execution code from running in live preview mode.
- **Default Locked State**: `ENABLE_LIVE_ANALYZE_PREVIEW` and `ENABLE_LIVE_SCOUT_PREVIEW` remain `false` by default.
- **No Automated Loops**: Manual endpoints allow single requests only; no repeated scanning, no scheduler.
- **No Production Database**: Read-only gates remain active. Operations only use the sandbox database (`tasi_ledger_test.db`).
- **No Telegram Alerts**: Telegram alert integration remains completely disabled for live preview modes.

## Added & Modified Files
- `backend/core/execution_guard.py`: Contains `assert_no_execution_allowed()` guard.
- `backend/api/system.py`: Added `/api/system/live-preview-status` and updated `/api/system/safety-matrix`.
- `backend/api/analyze.py` & `backend/api/scout.py`: Injected `assert_no_execution_allowed()` checks.
- `backend/api/live_preview.py`: Injected execution guards.
- `src/pages/Pages.tsx`: Added Live Preview Status component to Settings page.
- `scripts/live_preview_status.sh`: Shell script to query preview configuration.
- `scripts/live_preview_enable_notes.sh`: Informational notes on how to safely enable manual preview.
- `scripts/live_preview_negative_tests.sh`: Validation script testing boundary enforcements.
- `backend/tests/test_phase6u.py`: Pytest suite to validate safe states.

## How to Check Live Preview Status
You can check the current preview status by running:
```bash
bash scripts/live_preview_status.sh
```

## How to Manually Enable
Modify the `.env` on your VPS to set:
```
ENABLE_LIVE_ANALYZE_PREVIEW=true
ENABLE_LIVE_SCOUT_PREVIEW=true
```

**CRITICAL:**
- `ENABLE_ALERT_SCHEDULER` must remain `false`.
- `ENABLE_PROVIDER_COVERAGE_SCAN` must remain `false`.
- `ALLOW_PRODUCTION_DB` must remain `false`.

## Next Phase
**Phase 6V** - Market Data Provider Validation & Fallback Hardening
