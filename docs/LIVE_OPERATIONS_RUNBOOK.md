# Live Operations Runbook

Operating GHBS Trading — TASI Quant Command Center as a private live web app.
Access is Tailscale-only (`http://100.103.58.118:8080`). Public exposure stays blocked.

## Daily operation (Private Live Mode)
1. Confirm mode: sidebar/topbar badge shows **PRIVATE LIVE** (or LOCKED / AUTOMATED ALERTS).
   Cross-check `GET /api/system/operating-mode`.
2. Dashboard → Command Center: review Operating Mode panel, risk snapshot, and charts.
3. Market Data → run quote / OHLCV checks (gated by the live profile).
4. Analyze / Scout → run **read-only** live previews (no execution, no alerts, no DB writes).

## Telegram
- **Enable sending:** set `ENABLE_TELEGRAM_SEND=true` (+ `ENABLE_TELEGRAM_TEST_SEND=true`
  for the manual test-send), configure `TELEGRAM_BOT_TOKEN`/`TELEGRAM_TOKEN` +
  `TELEGRAM_CHAT_ID` in the VPS `.env`, restart.
- **Verify:** Alert Center → Telegram Readiness panel shows token source + gate status;
  send a manual/test alert; confirm it appears in the Alert Delivery Log.
- **Disable:** set both flags to `false`, restart. The manual test-send requires the
  scheduler to be OFF (mutually exclusive with scheduled sends by design).

## Scheduler (Automated Alert Mode)
- **Manual dry-run:** with `ENABLE_ALERT_SCHEDULER=true`, use the Alert Center controls
  (Start Dry Run / Send Dry Run Now). When the flag is false the controls are disabled
  with the helper text "Scheduler is locked because ENABLE_ALERT_SCHEDULER=false."
- **Automated:** keep `ALERT_SCHEDULER_DRY_RUN_ONLY=true` unless real scheduled sends are
  explicitly approved. Real scheduled sending is not implemented and never auto-starts on boot.

## Providers
- Configure keys in the VPS `.env` only (`TWELVEDATA_API_KEY`, etc.). See
  `docs/PROVIDER_API_SETUP.md`. Provider Health cards/endpoint show configured/ready/
  missing/locked with no key values.

## Keep production DB read-only
- `ALLOW_PRODUCTION_DB=false`, `PRODUCTION_DB_READONLY_REQUIRED=true`, `DB_PATH=tasi_ledger_test.db`.
- There is no write path to any production DB in the app.

## Restore LOCKED / MAINTENANCE
- Set every `ENABLE_*` gate to `false`, restart. Badge shows **LOCKED / MAINTENANCE**.

## What remains impossible (by design)
- Trade execution · broker execution · production DB writes · public exposure.
