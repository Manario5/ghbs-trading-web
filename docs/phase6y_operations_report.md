# Phase 6Y Operations Report

**Date:** 2026-07-18  
**Phase:** 6Y  
**Status:** Completed on VPS  
**Tag:** phase-6y-approved (baseline: phase-6x-approved @ 3ee1c8a)

---

## Runtime Environment

| Property | Value |
|---|---|
| Host | VPS (private access via Tailscale) |
| Tailscale IP | 100.103.58.118 |
| Port | 8080 |
| Public IP exposure | Blocked |
| App folder | /root/ghbs-trading-web-sandbox-6y |
| Process manager | systemd |
| .env location | /root/ghbs-trading-web-sandbox-6y/.env (not committed, gitignored) |

---

## Safety Matrix (Phase 6Y runtime state)

| Flag | Value |
|---|---|
| ALLOW_PRODUCTION_DB | false |
| DB_PATH | tasi_ledger_test.db |
| ENABLE_LIVE_ANALYZE_PREVIEW | false |
| ENABLE_LIVE_SCOUT_PREVIEW | false |
| ENABLE_ALERT_SCHEDULER | false |
| ENABLE_PROVIDER_COVERAGE_SCAN | false |
| ENABLE_MARKET_DATA_SMOKE_TESTS | false |
| ENABLE_TELEGRAM_SEND | false |
| ENABLE_TELEGRAM_TEST_SEND | false |
| telegram_dry_run_enabled | true |
| Safety state | **SAFE** |

No production database access was enabled. No Telegram messages were sent. No live market data calls were made.

---

## Secret Configuration (masked — no values)

Secrets are stored exclusively in the VPS `.env` file, which is gitignored. The following fields were present (configured/not configured only — values are never logged or committed):

| Secret | Status |
|---|---|
| TELEGRAM_BOT_TOKEN or TELEGRAM_TOKEN | configured |
| TELEGRAM_CHAT_ID | configured |
| AUTHORIZED_USER_IDS | configured |
| ANTHROPIC_API_KEY | configured |
| TWELVEDATA_API_KEY | configured |
| SAHMK_API_KEY | not configured |
| TRADINGVIEW_API_KEY | not configured |

The backend `/api/system/secret-status` and `/api/system/safety-matrix` endpoints return boolean or masked string values only — raw secret values are never included in any API response.

---

## Phase 6Y Changes Deployed

1. **Telegram token alias support** (`TELEGRAM_TOKEN` as fallback for `TELEGRAM_BOT_TOKEN`) — implemented in `backend/core/secrets.py` and `backend/core/telegram_readiness.py`.
2. **Safety matrix extended fields** — `telegram_token_source`, `telegram_token_alias_configured`, `telegram_token_alias_used` added to `/api/system/safety-matrix` response.
3. **Secret status endpoint** — `/api/system/secret-status` returns structured boolean-only secret presence report.
4. **Phase 6X tests** — `backend/tests/test_phase6x.py` validates alias fallback behavior end-to-end.

---

## Known Pre-existing Test Failures

The following test files fail to collect due to missing `pytest-asyncio` in the CI environment — these failures predate Phase 6Y and are not regressions:

- `backend/tests/test_core.py` — async tests require `pytest-asyncio`
- `backend/tests/test_phase6u.py` — async tests require `pytest-asyncio`
- `backend/tests/test_api.py` — import error (unrelated dependency)
- `backend/tests/test_api_v2b.py` — import error (unrelated dependency)
- `backend/tests/test_live_preview.py` — import error (unrelated dependency)

All synchronous tests (34 total) pass, including all phase-specific tests (6V, 6W, 6X, secrets).

---

## Phase 6Z Follow-up (this commit)

**Bug fixed:** `telegram_configured_masked` in the safety matrix previously checked only `TELEGRAM_BOT_TOKEN`, ignoring the `TELEGRAM_TOKEN` alias. This meant environments using the alias would show `"not configured"` incorrectly.

**Fix location:** `backend/api/system.py` line 49 — now checks both env vars via OR logic.

**Tests added:** `backend/tests/test_phase6z.py` — 6 tests covering:
- Configured via primary token → `"configured"`
- Configured via alias only → `"configured"`
- Neither set → `"not configured"`
- Whitespace-only alias → `"not configured"`
- No secret value leaks in safety-matrix response
- No secret value leaks in secret-status response

---

*This report contains no secret values. All credentials remain exclusively in the VPS `.env` file.*
