# Phase 6A: Live-Data Analyze Preview — Read-Only Sandbox

## Overview
Phase 6A bridges the static Market Data configurations established in Phase 5 with the quantitative modeling engine (Analyze). It introduces a strictly read-only, non-executable capability enabling real-time preview of a given asset's regime context, setup condition, and prospective sizing properties utilizing real provider OHLCV payloads mapped appropriately against simulated indicator criteria.

## Deliverables & Files Changed

### 1. Environment Configurations (`.env.example`)
* Integrated `ENABLE_LIVE_ANALYZE_PREVIEW=false` to gate the execution of live-data preview separately from standard diagnostic pathways.
* Set standard boundaries `LIVE_ANALYZE_LOOKBACK_DAYS=180` and `LIVE_ANALYZE_MIN_REQUIRED_BARS=120`.

### 2. Backend Live-Preview Module (`backend/api/live_preview.py`)
* Deployed protected endpoint `POST /api/live-preview/analyze/{ticker}`.
* Imported standard quantitative modules `classify_setup`, `compute_regime`, and `SizingEngine`. 
* Fetches `MarketDataService.test_historical_ohlcv()` checking array viability (columns and required counts).
* Blended extracted `latest_close` and `latest_volume` parameters cleanly into `get_mock_stock_data()` ensuring logic pipeline stability devoid of full DB requirements.
* Guaranteed properties: `sandbox_only=true`, `execution_allowed=false`.

### 3. Execution Mechanics (`backend/api/router.py`)
* Hooked the live-preview module elegantly onto internal `api_router` namespaces safely bypassing live tracking or persistence operations entirely.

### 4. Interactive UX Layout (`src/pages/Analyze.tsx`)
* Developed dedicated "Live Data Preview" pane segregated distinctly below standard Mocked Sandbox mechanics.
* Exposed `Run Live Preview` triggers feeding real provider OHLCV streams into standard GUI formats reporting Regime, Setup Type, and Data Quality directly.
* Enforced pervasive UI warning loops confirming "LIVEDATA PREVIEW • SANDBOX ONLY • NO EXECUTION • NO ALERTS • NOT USED FOR TRADE RECORDING" across all relevant views.

## Technical Safeguards Assured
* **No Database Operations**: Preview mechanics inherently bypass all inserts, journals, or trade ledger invocations ensuring `tasi_ledger.db` safety mathematically.
* **No Telemetry Additions**: Internal scheduler routines + Discord hook alerts remained isolated completely from Preview queries.
* **Existing Logic Unaltered**: Strategy constraints inside `TradeExecutor`, `classify_setup`, and sizing definitions maintain their precise Phase 4 configurations globally.

## Operational Test Workflow (VPS)
1. Verify module is enabled utilizing `.env` parameter `ENABLE_LIVE_ANALYZE_PREVIEW=true` ensuring prerequisites from Phase 5 are similarly flagged.
2. Visit `Analyze` dashboard noting distinct partition separating "Analyze (Sandbox)" defaults from the indigo-capped "Live Data Preview".
3. Submit `2222` triggering historical proxy retrieval evaluating valid price endpoints correctly parsing predicted Signal and Regime.
4. Verify absolute omission of `Create Sandbox Buy Ticket` buttons ensuring zero execution transitions inadvertently slip into preview pipelines.
5. Review explicit data-quality boundaries asserting array fields successfully retrieved bypassing any production consequences cleanly.

## Retest Insights & Fixes (VPS)
- Fixed an issue where yfinance sometimes returned untyped rows or empty boundaries leading to Python `NaN` scalars. We now aggressively enforce dataframe schema boundaries via `.dropna(subset=["Close"])` rendering explicitly safe numeric boundaries directly averting any 500 JSON translation errors. 
- Implemented robust `sanitize_for_json` layer intercepting any unpredictable `NaN`, `Infinity`, or mismatched NumPy mappings rendering safely to standard HTTP formats before egress.
- Corrected frontend UX behavior properly clearing cached/stale `liveData` states correctly mapping to "No live preview result available." during API fault lines securing visual presentation integrity securely. 
- Kept UI null formats natively rendered as explicit `'N/A'` representations isolating frontend parsing logic safely mitigating any crashes derived from potentially untyped objects natively tracking data quality gracefully.
