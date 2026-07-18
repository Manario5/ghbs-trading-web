# Phase 4B: Manual Alert Foundation Report

## Overview
Phase 4B establishes a foundation for manual Telegram alert notifications using the separate web-app Telegram bot. This functionality is distinctly separated from automated scheduling or live signal execution, acting purely as a secure verification of the alert delivery pipeline in sandbox mode.

## Deliverables & Files Changed

### 1. Backend Route (`backend/api/alerts.py`)
* Created a dedicated `alerts` router.
* Added `POST /api/alerts/manual-test` endpoint:
  * Leverages existing `WEBAPP_TELEGRAM_BOT_TOKEN` and `WEBAPP_TELEGRAM_CHAT_ID` explicitly.
  * Dispatches a hardcoded sandbox message confirming test execution timestamp.
  * Ensures compliance with sandbox boundaries through the `ENABLE_API_SMOKE_TESTS` requirement logic.
  * Optionally logs the manual request directly to the `audit_events` SQL table (acting strictly as a notification event, not a trading event).

### 2. Router Registration (`backend/api/router.py`)
* Registered the newly constructed `backend/api/alerts.py` logic under `/api/alerts`.

### 3. Frontend Settings UI (`src/pages/Pages.tsx`)
* Appended a dedicated "Manual Alerts" card below the Integration Status block inside Settings view.
* Implemented the **"Send Manual Telegram Alert"** ping interface.
* Emphasized UX transparency: "Manual notification test only. No trading action, no scheduler, and no live signal execution."

## Security & Architectural Constraints
* **No Production Database Overrides**: `ALLOW_PRODUCTION_DB=false` and default variables structurally map towards `tasi_ledger_test.db`.
* **No Live Telegram Tracking**: We exclusively use the web-app bot layer token. No integration exists regarding the primary live trading Telegram bot logic. 
* **Zero Autonomous Scheduling**: Not implemented.
* **No Market API Usage**: No yfinance, TwelveData, or TradingView structures were modified.
* **No Structural Engine Modification**: All strategy execution remains rigidly within Phase 3 properties.
* **Secured Outputs**: Secrets are managed correctly by environment isolation.

## Test Instructions (VPS Environment)
1. Verify `ENABLE_API_SMOKE_TESTS=true` inside your `.env` settings along with the `WEBAPP_TELEGRAM_*` tokens.
2. Ensure `uvicorn backend.main:app` daemon reload has captured the new `/alerts` endpoints.
3. Access the `Settings` page via frontend.
4. Expand the "Manual Alerts" module and execute **"Send Manual Telegram Alert"**.
5. Log receipt of the "GHBS TASI Web App Manual Alert Test [time]" inside the matching Telegram group constraint.

## Validation checks
* Frontend logic validates successfully spanning standard production-mode checks (`npm run build` & `npx tsc --noEmit`).
* Standard Pytest logic structure remains resilient towards `/alerts` API additions but manual testing overrides natively enforce security rules inside VPS layers.
