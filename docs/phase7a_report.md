# Phase 7A Report — Controlled Telegram Manual Test-Send

**Date:** 2026-07-18  
**Phase:** 7A  
**Branch:** claude/ghbs-tasi-phase-7a-telegram-test-send  
**Base commit:** 38f4137 (phase-6z-approved)  
**Status:** Implementation complete — pending VPS review before tag

---

## What Was Implemented

Phase 7A adds a controlled, gate-guarded manual Telegram test-send capability. No automatic or scheduled sends exist. Real Telegram network calls are made only when every explicit gate is open.

### New files

| File | Purpose |
|---|---|
| `backend/core/telegram_sender.py` | Controlled sender module; evaluates all gates before any HTTP call |
| `backend/tests/test_phase7a.py` | 16 tests covering all gate paths, secret leak prevention, and endpoint behavior |
| `docs/phase7a_report.md` | This report |

### Modified files

| File | Change |
|---|---|
| `backend/api/alerts.py` | Added `POST /api/alerts/telegram/test-send` endpoint |
| `backend/core/telegram_readiness.py` | `get_telegram_alert_status()` now includes Phase 7A gate fields |
| `backend/api/system.py` | Safety matrix exposes Phase 7A gate-status fields |
| `.env.example` | Documented Phase 7A gate flags with safe defaults |

---

## Five-Gate Model

A real Telegram network call is made only when **all five gates** are simultaneously open:

| Gate | Environment Variable | Required Value |
|---|---|---|
| 1 | `ENABLE_TELEGRAM_TEST_SEND` | `true` |
| 2 | `ENABLE_TELEGRAM_SEND` | `true` |
| 3 | `ENABLE_ALERT_SCHEDULER` | `false` (scheduler must be OFF) |
| 4 | Token configured | `TELEGRAM_BOT_TOKEN` or `TELEGRAM_TOKEN` non-empty |
| 5 | Chat ID configured | `TELEGRAM_CHAT_ID` non-empty |

If any gate is not satisfied, `evaluate_test_send_gates()` returns `can_run_test_send: false` and the endpoint returns a locked response with no network call. The `blocked_reasons` list names exactly which gate(s) failed.

---

## Default State (SAFE)

The `.env.example` default and the VPS `.env` both have:

```
ENABLE_TELEGRAM_SEND=false
ENABLE_TELEGRAM_TEST_SEND=false
ENABLE_ALERT_SCHEDULER=false
```

With these defaults, the safety matrix returns `safety_state: SAFE` and `can_run_test_send: false`.

---

## New API Endpoints

### `POST /api/alerts/telegram/test-send`

Requires authentication. Returns a JSON object — never includes token or chat ID values.

**Locked response (default):**
```json
{
  "sent": false,
  "dry_run": true,
  "network_call_made": false,
  "gate_status": "locked",
  "can_run_test_send": false,
  "test_send_requires_manual_enablement": true,
  "network_call_allowed_for_test_send": false,
  "blocked_reasons": ["ENABLE_TELEGRAM_TEST_SEND is false", "ENABLE_TELEGRAM_SEND is false"],
  "message": "Test-send is locked. All gates must be manually enabled. No network call was made."
}
```

**Open response (all gates true, success):**
```json
{
  "sent": true,
  "dry_run": false,
  "network_call_made": true,
  "gate_status": "open",
  "can_run_test_send": true,
  "test_send_requires_manual_enablement": false,
  "network_call_allowed_for_test_send": true,
  "blocked_reasons": [],
  "target_chat_masked": "***1234",
  "message": "Test message sent successfully.",
  "timestamp": "2026-07-18T..."
}
```

---

## New Safety Matrix Fields

The `GET /api/system/safety-matrix` response now includes:

| Field | Default value | Meaning |
|---|---|---|
| `can_run_test_send` | `false` | All gates satisfied |
| `test_send_gate_status` | `"locked"` | `"open"` or `"locked"` |
| `test_send_requires_manual_enablement` | `true` | Manual VPS .env edit required |
| `network_call_allowed_for_test_send` | `false` | Whether HTTP call is permitted |

---

## Manual VPS Procedure (when authorized)

To perform a controlled test send on the VPS:

1. SSH into VPS, navigate to `/root/ghbs-trading-web-sandbox-6z`
2. Edit `.env` — set the following (do not commit this file):
   ```
   ENABLE_TELEGRAM_TEST_SEND=true
   ENABLE_TELEGRAM_SEND=true
   ENABLE_ALERT_SCHEDULER=false
   ```
3. Restart the backend service:
   ```
   systemctl restart ghbs-backend
   ```
4. Use the app UI or curl (via Tailscale) to POST to `/api/alerts/telegram/test-send`
5. Verify message received in Telegram
6. Immediately restore `.env` to safe defaults and restart again

**Never enable `ENABLE_ALERT_SCHEDULER=true` during a manual test send.**

---

## Test Summary

All 16 Phase 7A tests pass. No regressions in the existing 50 synchronous tests.

| Test | Outcome |
|---|---|
| Default state: all gates locked | PASS |
| Missing token blocks send | PASS |
| Missing chat ID blocks send | PASS |
| Scheduler enabled blocks send | PASS |
| ENABLE_TELEGRAM_SEND=false blocks | PASS |
| ENABLE_TELEGRAM_TEST_SEND=false blocks | PASS |
| All gates open → `can_run_test_send: true` | PASS |
| Alias token satisfies token gate | PASS |
| Sender locked → no network call | PASS |
| Sender open → HTTP POST called (mocked) | PASS |
| No secret values in sender result | PASS |
| Endpoint locked by default (sync client) | PASS |
| Safety matrix exposes Phase 7A fields | PASS |
| No secret leak in safety-matrix response | PASS |
| No authorized IDs leak in response | PASS |
| Safety state SAFE with all sends disabled | PASS |

---

## Secret Handling

- Token and chat ID values are never included in any API response
- `telegram_bot_token_masked` returns `"configured"` or `"missing"` only
- `target_chat_masked` returns `***` + last 4 digits only
- Authorized user IDs are count-only in all responses
- `.env` file remains gitignored; no secrets were committed

---

*This report contains no secret values.*
