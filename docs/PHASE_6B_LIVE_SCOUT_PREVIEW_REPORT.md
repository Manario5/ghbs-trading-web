# Phase 6B: Live-Data Scout Preview — Read-Only Sandbox

## Overview
Phase 6B introduces the capability to run a market-wide "Scout" execution leveraging live-data endpoints. Continuing the strict safety parameters enforced in Phase 6A, this preview mode operates entirely securely rendering an array sequence mapping current quantitative strategies across up to 10 tickers within the TASI 80 universe payload independently mapping Live signals natively without writing actions or altering the existing Mock sandbox environments.

## Deliverables & Files Changed

### 1. Environment Configurations (`.env.example`)
* Exposed boundary mechanics: 
  * `ENABLE_LIVE_SCOUT_PREVIEW=false`
  * `LIVE_SCOUT_LOOKBACK_DAYS=180`
  * `LIVE_SCOUT_MIN_REQUIRED_BARS=120`
  * `LIVE_SCOUT_LIMIT=10`

### 2. Backend API Endpoint (`backend/api/live_preview.py`)
* Deployed protected `POST /api/live-preview/scout` ensuring strict constraint gating (verifying internal API prerequisites such as `ENABLE_MARKET_DATA_SMOKE_TESTS` + `ENABLE_OHLCV_DIAGNOSTICS` mapping to `ENABLE_LIVE_SCOUT_PREVIEW`).
* Integrated array logic natively parsing `LIVE_SCOUT_LIMIT` boundaries slicing independent `yfinance_symbol` components appropriately.
* Sanitized output constraints ensuring Python scalars (`NaN`, `Infinity`, `Pandas NA`) gracefully convert to `null` tracking warnings securely ensuring JSON payload outputs omit `500 Internal Server Errors`.

### 3. Frontend UI Component (`src/pages/Scout.tsx`)
* Instantiated segregated "Live Data Scout Preview" mapping underneath conventional sandbox testing tables enforcing UI partitions explicitly.
* Outlaid visual "Summary Tiles" representing `Scanned`, `Eligible`, `Blocked`, and `Data Failures` safely decoupling status parameters natively without overlapping standard mock boundaries.
* Designed HTML Table constructs visually reporting Regime, Setup, Signal endpoints alongside health tracking explicitly omitting standard "Ticket" / "Plan" / "Watch" execution triggers mitigating inadvertent triggers securely.

## Technical Safeguards Assured
* **No Database Operations**: Preview routines inherently bypass `tasi_ledger.db` transactions natively rendering 0 alterations globally.
* **No Telemetry Extensions**: Alert mechanics / Action plans decoupled dynamically verifying zero notification boundaries.
* **Fallback Safety**: Null values inherently capture gracefully within UI frameworks bypassing raw trackbacks completely ensuring "N/A" mappings render naturally supporting edge cases accurately.

## Operational Test Workflow (VPS)
1. Edit `.env` ensuring `ENABLE_LIVE_SCOUT_PREVIEW=true` mapping explicit prerequisites efficiently.
2. Visit `Scout` interface observing "Live Data Scout Preview" table decoupled directly.
3. Initiate "Run Live Scout Preview" parsing live data payloads sequentially observing Table populations representing Real-Time price points effectively scaling logic schemas.
4. Verify "N/A" formatting during OHLCV boundaries (or `FAIL` values representing empty arrays).
5. Ensure zero database modifications or alert components fire upon table creation accurately verifying sandbox separation limits precisely.

## Retest Insights & Fixes (VPS)
- Fixed an issue where the `Sector / Tier` columns in the Live Scout Preview table displayed as "Unknown / Unknown". We integrated `SECTOR_MAP` and `TIER_MAP` directly from `backend.core.universe` to accurately populate the sector and tier fields on live-data queries for mapped tickers (e.g., mapping 1120 to Banks/TIER_1).
- Updated the frontend column label from "Provider" to "Provider Ticker" to correctly describe the output rendered in that column.
