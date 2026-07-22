# Private Live Profile

How to enable/disable Private Live Mode via the VPS `.env`. See
`.env.live.example` for the copy-paste values. No secrets belong in git.

## Enable Private Live Mode
Set these in the VPS `.env`, then restart the backend:
```
ENABLE_API_SMOKE_TESTS=true
ENABLE_MARKET_DATA_SMOKE_TESTS=true
ENABLE_PROVIDER_COVERAGE_SCAN=true
ENABLE_OHLCV_DIAGNOSTICS=true
ENABLE_LIVE_ANALYZE_PREVIEW=true
ENABLE_LIVE_SCOUT_PREVIEW=true
ENABLE_TELEGRAM_DRY_RUN=true
ENABLE_TELEGRAM_SEND=true
ENABLE_TELEGRAM_TEST_SEND=true
```
Provider/Telegram/Anthropic **keys** go only in the VPS `.env`, never in git.

## Enable Automated Alert Mode (optional)
```
ENABLE_ALERT_SCHEDULER=true
ALERT_SCHEDULER_DRY_RUN_ONLY=true   # false only for approved real sends
```

## Keep production DB read-only (mandatory)
```
ALLOW_PRODUCTION_DB=false
PRODUCTION_DB_READONLY_REQUIRED=true
DB_PATH=tasi_ledger_test.db
```
Production DB writes are impossible regardless of these values — there is no
write path in the app — but keep them set as defense in depth.

## Return to LOCKED / MAINTENANCE
Set every `ENABLE_*` gate above to `false` and restart. `GET
/api/system/operating-mode` will report `LOCKED_MAINTENANCE`.

## Verify
- `GET /api/system/operating-mode` → expected `mode_label`
- UI sidebar/topbar badge reflects the mode
- `GET /api/system/safety-matrix` → SAFE (locked) or WARNING (live gates on),
  never UNSAFE unless a dangerous condition exists
