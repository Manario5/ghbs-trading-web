# Phase 4C: Alert Templates and Manual Alert Log Report

## Overview
Phase 4C expands upon manual alerts by introducing configurable Sandbox Alert Templates and a persistent Sandbox Log. This provides safe preconfiguration checks over payload structures without engaging live signal execution layers. 

## Deliverables & Files Changed

### 1. Database and Architecture (`backend/db/database.py`)
* Created the `alert_events` table natively capturing structual notification payloads without connecting to production `tasi_ledger.db`.
* Fields included: `alert_type`, `title`, `message`, `delivery_status`, `destination_masked`, `created_by`, `created_at`.
* Kept default connections enforced to `tasi_ledger_test.db` and `ALLOW_PRODUCTION_DB=false`.

### 2. Backend Alerts API (`backend/api/alerts.py`)
* Introduced internal proxy logger `log_alert_event()` which dynamically inserts alerts payload references towards the `alert_events` table.
* Added protected structural endpoints:
  * `POST /api/alerts/send-template`: Evaluates template payloads dynamically and pings Telegram securely leveraging the dedicated `WEBAPP_TELEGRAM_BOT_TOKEN`, avoiding interference with live operational bots.
  * `GET /api/alerts/log`: Restores history from the `alert_events` sandbox table.

### 3. Frontend Alert Center UI (`src/pages/AlertCenter.tsx`, `src/App.tsx`, `src/pages/Layout.tsx`)
* Instantiated an entirely separated `/alerts` route mapping.
* Connected `AlertCenter` to navigation (`Layout.tsx`) resolving rendering via Telegram Icon inside sidebar block.
* Included Template configurations masking operational signals safely: 
  * General Test Alert
  * Scout Summary Test
  * Action Plan Reminder Test
  * TP Hit Test
  * Stop Alert Test
* Hardcoded Warning Display: "Manual alert only. No scheduler, no live signal, no trade execution."

## Security & Concurrency Verification
* **No Exposing Secrets**: Telegram secrets stay bound within backend `.env` variables cleanly avoiding any React hydration scope leakage.
* **No Background Schedulers**: Tests fire exclusively on demand. 
* **Safe State Context**: Execution requires `ENABLE_API_SMOKE_TESTS=true` inside `.env`.
* **Zero Trading Engine Impact**: Models, rules and execution criteria remain rigidly separated as built during Phase 3. No live positions interact with this manual system.

## Test Instructions (VPS Environment)
1. Verify `ENABLE_API_SMOKE_TESTS=true` is operational inside backend `.env`.
2. Map your Webapp API keys natively: `WEBAPP_TELEGRAM_BOT_TOKEN` and `WEBAPP_TELEGRAM_CHAT_ID`. Note: **Do not** utilize the active telegram bot processing the live TASI logic!
3. Re-start the `uvicorn backend.main:app` daemon safely.
4. Launch the `Alert Center` page via the command center navigation.
5. Cycle through manual templates safely evaluating correct target masking on Log views natively reporting either `SENT`/`FAILED` boundaries independently.

## Executed Pipeline Verification
* Compiled safely via `npm run build` bridging with isolated type checks locally resolving `npx tsc --noEmit`. 
* Standard verification via `pytest backend/tests` is safely delegable towards developers prior to merging.

## Issues Fixed After VPS Testing
* **Telegram 400 Error**: During testing, sending a template alert failed with a Telegram HTTP 400 Bad Request error.
* **Raw Token Exposure**: The frontend displayed the raw Telegram API error URL including the bot token because `str(e)` on an `httpx._exceptions.HTTPStatusError` exposed the URL.
* **Fix Applied**: 
  * Exception handlers in backend (for both `/send-template` and `/manual-test`) were updated to catch `httpx.HTTPStatusError` explicitly and return sanitized error strings (`"Telegram delivery failed. Check bot token, chat ID, or bot access."`) ensuring bot tokens or request URLs are never leaked via API responses or the database log.
  * The frontend `AlertCenter.tsx` was fixed to properly evaluate `res.data.success` allowing the UI to render the sanitized fallback messages appropriately.
