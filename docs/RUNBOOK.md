# GHBS Trading TASI Web App — Operations Runbook (Release Train F)

Access is Tailscale-only (`http://100.103.58.118:8080`). Public exposure is
blocked and must remain blocked. No secrets appear in this document.

## 1. Deployment
1. Fetch the reviewed branch/tag into a NEW sandbox folder (never overwrite the running one):
   ```
   git clone <repo> /root/ghbs-trading-web-sandbox-<name>
   cd /root/ghbs-trading-web-sandbox-<name> && git checkout <reviewed-ref>
   ```
2. Copy `.env` from the previous runtime folder (never from git).
3. Install: `pip install -r requirements-webapp.txt && npm ci && npm run build`
4. Validate: `bash scripts/run_full_validation.sh`
5. Point the systemd unit at the new folder; `systemctl daemon-reload && systemctl restart <service>`
6. Verify: `GET /api/system/health-deep` → ok, `GET /api/system/safety-matrix` → SAFE.

## 2. Rollback
1. Point systemd back at the previous folder; restart.
2. Verify health-deep + safety-matrix as above.
3. See also `docs/RELEASE_TRAIN_A_ROLLBACK.md` for the additive-change rationale.

## 3. Secrets setup (VPS `.env` only)
- `.env` lives only in the runtime folder, is gitignored, mode 600.
- Never echo, cat into logs, or commit it. Verify masking after any change via
  `GET /api/system/secret-status` (booleans only).

## 4. API connections (all through env vars; all locked by default)
| API | Env vars | Readiness check (masked) |
|---|---|---|
| Anthropic | `ANTHROPIC_API_KEY` | `/api/system/secret-status` → `anthropic.configured` |
| Telegram Bot | `TELEGRAM_BOT_TOKEN` (or `TELEGRAM_TOKEN`), `TELEGRAM_CHAT_ID`, `AUTHORIZED_USER_IDS` | `/api/alerts/telegram/status` |
| TwelveData | `TWELVEDATA_API_KEY` | `/api/market-data/provider-health` |
| Sahmk | `SAHMK_API_KEY` | `/api/market-data/provider-health` (readiness only) |
| TradingView | `TRADINGVIEW_API_KEY` | `/api/market-data/provider-health` (readiness only) |

Procedure for any key: edit `.env` → restart service → check the masked
readiness endpoint → never enable a send/test flag at the same time as adding a key.

## 5. Telegram setup & manual test-send
See `docs/phase7a_report.md` (five-gate model) and
`docs/RELEASE_TRAIN_A_RUNTIME_VERIFICATION.md` §4 for the controlled
test-send procedure. Always restore flags to false immediately after.

## 6. Provider setup
See `docs/PROVIDER_API_SETUP.md`.

## 7. Production DB read-only setup (Train F scope, still approval-gated)
- `PRODUCTION_DB_PATH=<path>` (read target), `ENABLE_PRODUCTION_DB_READONLY_GATE=true`,
  `PRODUCTION_DB_READONLY_REQUIRED=true` must stay true.
- `ALLOW_PRODUCTION_DB` must remain `false` — the gate reads, never attaches for writes.
- Verify via safety matrix fields `production_db_*` after restart.

## 8. Scheduler activation
See `docs/SCHEDULER_ACTIVATION.md`. Real scheduled sends are not implemented;
activation requires a separate approved change.

## 9. Safety verification (after ANY change)
1. `GET /api/system/safety-matrix` → `safety_state: "SAFE"`
2. `GET /api/system/ops-status` → `overall_state: "SAFE"`; skim every section for `locked`
3. `POST /api/alerts/telegram/test-send` → locked, `network_call_made: false`
4. `bash scripts/run_full_validation.sh` in the runtime folder
5. Confirm the app is unreachable from the public internet (curl from outside Tailscale must fail)

## 10. Backup / restore
- Backup: `bash scripts/backup_sandbox.sh /root/ghbs-trading-web-sandbox-<name>`
  (tarballs test ledger, audit file, `.env` into `backups/`, mode 600, VPS-only)
- Restore: `bash scripts/restore_sandbox.sh <tarball> <app-dir>` (refuses to
  overwrite without `--force`), then restart + safety verification.
- Suggested cadence: daily cron on the VPS + before every deployment.
