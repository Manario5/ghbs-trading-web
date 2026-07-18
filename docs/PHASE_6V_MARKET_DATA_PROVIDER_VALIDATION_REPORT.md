# Phase 6V - Market Data Provider Validation & Fallback Hardening

## Overview
This phase builds a safe market data provider readiness layer. It enables the system to report on which market data providers (yfinance, TwelveData, Sahmk, TradingView) are configured and available in the environment, and establishes a clear fallback order, **without** performing any live network calls or executing any market data strategies by default.

## Safety Guarantees
- **No API Calls by Default**: `provider_calls_locked` remains true until specifically unlocked by enabling smoke tests, coverage scan, or live previews.
- **Secrets are Masked**: API keys for TwelveData, Sahmk, and TradingView are strictly checked for existence only (`bool(key)`). The actual keys are never included in the JSON response, logs, or UI.
- **Execution Remains Blocked**: Smoke test endpoints or coverage scans (if implemented in future phases) are strongly guarded by environment flags (`ENABLE_MARKET_DATA_SMOKE_TESTS`, `ENABLE_PROVIDER_COVERAGE_SCAN`).
- **No Strategy Changes**: The core TASI engine and setup classifications remain completely untouched.
- **Sandbox Unchanged**: Production database paths, scheduler flags, and telegram alerts remain blocked.

## Files Added/Modified
- `backend/core/provider_readiness.py`: Implements readiness status logic and secret masking.
- `backend/api/system.py`: Added `/api/system/provider-readiness-status` endpoint and enhanced `/api/system/safety-matrix`.
- `src/pages/Pages.tsx`: Added Provider Readiness Status card to the system dashboard settings page.
- `scripts/provider_readiness_status.sh`: Shell script to quickly check readiness from VPS console.
- `scripts/provider_negative_tests.sh`: Validation tests to ensure defaults are locked and safe.
- `scripts/provider_manual_smoke_notes.sh`: Instructions for manually testing providers in isolation.
- `scripts/validate_release.sh`: Added the provider negative tests to the release checklist.

## Provider Fallback Order
If multiple providers are configured, the system uses the following strict fallback order for market data:
1. `yfinance` (Default, no secrets required)
2. `twelvedata` (Requires `TWELVEDATA_API_KEY`)
3. `sahmk` (Requires `SAHMK_API_KEY`)
4. `tradingview` (Requires `TRADINGVIEW_API_KEY`)

## What Remains for Later Phases
- Actual implementation of the fallback logic across market data fetching clients.
- Implementing the real provider coverage scan mechanism.
- Building out live Telegram execution pipelines (Phase 6W/etc).
- Switching the live system to use the production database paths.
