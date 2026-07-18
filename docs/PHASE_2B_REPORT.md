# Phase 2B Report: Sandbox Engine API Integration

## What Was Connected
In Phase 2B, we successfully connected the FastAPI backend to the refactored `/backend/core` modules through a purely sandbox environment.
- **Service Layer**: A new `engine_service.py` was created to safely wrap the engine's core capabilities. It acts as an integration layer that isolates real modules (`TradeExecutor`, `SizingEngine.propose()`, `classify_setup()`, `compute_regime()`) from real data fetching. 
- **Endpoint Upgrades**: 
  - `POST /api/analyze/{ticker}` now drives mock stock data through the exact same classification filters and outputs detailed JSON (with sizing proposals).
  - `POST /api/scout/run` now evaluates a mock subset of the `WATCHLIST`, correctly processing sector breadths and applying regime calculation.
  - `POST /api/trades/buy` and `/api/trades/sell` directly proxy into our `TradeExecutor` with fake timestamps and data to mimic real interaction and enforce sandbox isolation.
  - `POST /api/risk/can-i-take-this-trade` correctly leverages system rules and config to simulate valid and invalid trade setups before hitting executions.

## What is Still Mocked
All HTTP/External integrations natively remain disabled or mocked:
- Data Providers (`yfinance`, `TwelveData`, `SAHMK`, `TradingView`) are skipped. Python generators supply `get_mock_stock_data()` with prefilled OHLCV buffers.
- `Claude API` is ignored. Instead, deterministic signal strings (`"BUY" / "HOLD"`) are synthetically assigned based on the mechanical pass/fail.

## Confirmations
- **No Production Database Access:** All endpoints explicitly derive `db_path` dynamically via `get_db_path()`, which defaults to `tasi_ledger_test.db` instead of `CFG.db_path`. We also added a hardcoded **Database Safety Guard** to reject startup if the database path attempts to load `tasi_ledger.db` directly unless overridden by an `ALLOW_PRODUCTION_DB=true` environment variable. This securely scopes testing and sandbox interactions away from the production state. Executing `/api/trades/buy` touches SQLite, but the transactions are never committed to `tasi_ledger.db`.
- **No External API Calls:** Zero HTTP traffic routes out. Not via `auth`, `Telegram`, or `Anthropic`.
- **No Strategy Changes:** Zero modifications occurred in `CFG`, TP logic or risk gates.
- **No Scheduler / Telegram Alert Bot Integration:** The background jobs do not exist inside FastAPI.
- **No Frontend Work:** Code architecture and JSON routing remain API-exclusive.
- **Removed Trades Deletion / Commission Overrides:** There is no `/api/trades/delete` and no custom user argument maps commission logic in Phase 2B endpoints.

## Operational Changes
- Transitioned FastAPI `_app.on_event("startup")_` to the modern parameterized `@asynccontextmanager lifespan(...)` generator. 
