# Phase 5C: Read-Only Historical OHLCV Diagnostics

## Overview
Phase 5C expands the market data testing foundation by implementing read-only historical OHLCV diagnostics. The goal is to verify that selected data providers return sufficient historical bars for the TASI universe, acting strictly as a data-quality check prior to integration into any trading strategies or analytical mechanics.

## Deliverables & Files Changed

### 1. Environment Configurations (`.env.example`)
* Added `ENABLE_OHLCV_DIAGNOSTICS` to securely toggle the read-only module.
* Added OHLCV query limits constraints: `OHLCV_SAMPLE_TICKER`, `OHLCV_LOOKBACK_DAYS=180`, `OHLCV_MIN_REQUIRED_BARS=120`.

### 2. Backend OHLCV Module (`backend/services/market_data_service.py`)
* Created `test_historical_ohlcv(ticker, lookback_days)`, simulating long-term query responses ensuring full array coverage (`Open`, `High`, `Low`, `Close`, `Volume`). 
* Extended universe polling via `test_universe_ohlcv_sample(limit)` fetching sample iteration bars mirroring the individual OHLCV handler.
* Implemented provider-specific behavior:
  * **yfinance**: Utilized `ticker.history` over specified lookback days securely encapsulating panda frame structures into standard JSON.
  * **twelvedata**: Configured `outputsize` parsing standard `time_series` endpoints gracefully reverting onto error validations.
  * **mock**: Simulated randomized array loops adhering to schema prerequisites identically mapping `bars_returned` successfully.

### 3. Diagnostics Endpoints (`backend/api/market_data.py`)
* Added `POST /api/market-data/test-ohlcv`.
* Added `POST /api/market-data/test-universe-ohlcv-sample`.
* Enforced rigid authentication and dual authorization (`ENABLE_MARKET_DATA_SMOKE_TESTS` + `ENABLE_OHLCV_DIAGNOSTICS`) successfully isolating parameters away from exposed logic returning `400` status loops natively.

### 4. Hardware/UX Additions (`src/pages/MarketData.tsx`)
* Incorporated independent `Historical OHLCV Diagnostics` UI segment immediately preceding the standalone Universe Mapping layouts.
* Constructed parameter display grids reflecting current provider properties (`Lookback Days: 180`).
* Added `Test OHLCV` tracking solitary symbol array results.
* Added `Test Universe OHLCV Sample` displaying table formats indicating explicitly missing metric fields avoiding hidden data traps (e.g., missing Volumes marked clearly).

## Technical Safeguards Assured
* **No Strategy Mechanics Implemented**: `classify_setup`, `compute_regime`, `SizingEngine`, etc., contain absolutely no crossover paths querying this data structure securely.
* **No Scout Integration**: Market data operates completely detached avoiding logic triggers remotely.
* **No Trading Operations**: `TradeExecutor` retains rigid ignorance regarding these mock payloads.
* **No Live Database Alterations**: Positions, journals, or events are entirely static without inserting mock structures over the production paths `tasi_ledger.db` specifically.

## Operational Test Workflow (VPS)
1. Verify module is enabled utilizing `.env` parameters `ENABLE_MARKET_DATA_SMOKE_TESTS=true` and `ENABLE_OHLCV_DIAGNOSTICS=true`.
2. Inspect "Historical OHLCV Diagnostics" component confirming `180` Lookback Days / `120` Min Required Bars load seamlessly.
3. Select "Test OHLCV" against `2222.SR`, confirming the single sample array outputs appropriately structured dates, counts (`bars_returned >= 120`), and correct validation variables across all five OHLCV strings.
4. Select "Test Universe OHLCV Sample" tracing iteration over standard TASI assets noting explicitly any API tier rejections (TwelveData specific) parsing as soft `safe_message` warnings preventing total stack collapses directly rendering.
