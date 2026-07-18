# Sandbox Environment Safety Checklist

This checklist confirms that the current application state explicitly prevents unintentional side effects during development phases.

## 1. Production DB Guard
- [x] Backend explicitly defaults to `tasi_ledger_test.db` if `ALLOW_PRODUCTION_DB` is not true.
- [x] No logic directly queries or updates `tasi_ledger.db`.
- [x] The `run_migrations()` utility only runs on the target DB path matching the boolean toggle.

## 2. API Key & Data Leakage 
- [x] No real financial or algorithmic APIs are in use (yfinance, TwelveData, SAHMK, TradingView).
- [x] Claude API keys are strictly omitted.
- [x] No `tasi_ledger.db` exports or credential dumps exist in frontend endpoints.
- [x] CSV Exports in `/history` specifically target generic mock blobs returned by the `/api/history` read-only views.

## 3. Communication Bots (Telegram)
- [x] No live Telegram bot integration is attached to the backend APIs.
- [x] No Telegram signals are queued, formatted, or dispatched.

## 4. Automation & Schedulers
- [x] No `APScheduler` or chron jobs execute standard trading algorithms at 10 AM.
- [x] The main `run_engine()` function acts procedurally on isolated endpoints rather than looping autonomously.

## 5. UI Guards
- [x] All major interactive pages (`/dashboard`, `/account`, `/portfolio`, `/performance`, `/history`, `/action-plan`, `/journal`, `/analyze`, `/scout`) contain a hardcoded `⚡ SANDBOX MODE` indicator.
- [x] Interactive models accurately frame buttons as "Simulation", "Sandbox Update", or "Mock Ticker".

## 6. Algorithmic Integrity
- [x] Core strategy logic / math modules remain pristine and unchanged by the Sandbox UI developments.
- [x] Trade deletion explicitly prohibited in generic context. Only `sandbox action-plan` and `sandbox journal` items possess a DELETE operation, tightly scoped to their generic UUIDs. No `DELETE /api/positions` endpoints exist. 
- [x] Commission overrides or manual PnL adjustments are locked out.

*Status: Verified OK & Locked.*
