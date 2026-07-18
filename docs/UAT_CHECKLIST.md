# Final UAT Checklist (Release Train F)

Run on the VPS over Tailscale after deploying the full implementation branch.
Every item must pass before go/no-go review.

## A. Baseline safety
- [ ] `GET /api/system/safety-matrix` → SAFE with default `.env`
- [ ] `GET /api/system/ops-status` → overall_state SAFE; all readiness sections locked
- [ ] `GET /api/system/health-deep` → status ok, db_connectivity true
- [ ] App unreachable from public internet
- [ ] `.env` not in git; `git status` clean of secrets/audit/backups

## B. Auth & core pages
- [ ] Login works; bad password rejected
- [ ] Dashboard, Positions, Performance, History, Journal, Action Plan load
- [ ] Analyze + Scout pages load (sandbox data)

## C. Alerts & Telegram (Train A)
- [ ] Alert Center shows Telegram Readiness panel: LOCKED badge, SAFE badge, blocked reasons
- [ ] `POST /api/alerts/telegram/test-send` → locked, no network call, audit entry written
- [ ] `GET /api/alerts/templates` lists ≥ 7 templates; render endpoint works
- [ ] Audit file contains masked data only

## D. Validation infra (Train B)
- [ ] `bash scripts/run_full_validation.sh` passes end-to-end on the VPS
- [ ] `python scripts/secret_scan.py` → CLEAN

## E. Market data (Train C)
- [ ] Market Data page shows Provider Readiness panel with NETWORK LOCKED badge
- [ ] `GET /api/market-data/provider-health` → network_calls_locked true, no key values
- [ ] With a TwelveData key configured (masked): effective chain shows yfinance → twelvedata

## F. Live preview (Train D)
- [ ] `GET /api/live-preview/readiness` lists exact blockers with default flags
- [ ] `GET /api/live-preview/sample-format` returns static sample marked sample:true
- [ ] `POST /api/live-preview/analyze/2222.SR` → 400 disabled by default

## G. Scheduler (Train E)
- [ ] Alert Center shows Scheduled Alerts Readiness panel: NOT RUNNING, SENDS LOCKED
- [ ] `GET /api/scheduler/readiness` → is_running false, gates locked, 3 jobs defined
- [ ] Restart the service; confirm scheduler still not running (no auto-start)

## H. Operations (Train F)
- [ ] `scripts/backup_sandbox.sh` produces a tarball; `restore_sandbox.sh` refuses overwrite without --force
- [ ] Runbook §9 safety verification passes end-to-end

## Sign-off
- Reviewer: ____________  Date: ____________  Commit: ____________
