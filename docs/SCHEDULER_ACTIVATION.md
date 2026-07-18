# Scheduler & Automated Alerts — Future Controlled Activation (Release Train E)

Train E ships **readiness only**. No scheduler starts by default, real
scheduled sends are NOT implemented (`real_scheduled_sends_implemented: false`),
and job definitions are declarative data, not running tasks.

## What exists now
- `backend/core/scheduler_readiness.py` — job registry + gate evaluation
- `GET /api/scheduler/readiness` — locked/running state, gates, blocked reasons
- Scheduled attempts are audited through the Train A audit layer (`kind: "scheduled"`)
- UI: Alert Center → Scheduled Alerts Readiness panel
- Existing dry-run scheduler (Phase 4B era) remains, still gated by
  `ENABLE_ALERT_SCHEDULER` and dry-run-only flags

## Gate model for REAL scheduled sends (future)
All of:
1. `ENABLE_ALERT_SCHEDULER=true`
2. `ENABLE_TELEGRAM_SEND=true`
3. Token configured (`TELEGRAM_BOT_TOKEN` or `TELEGRAM_TOKEN`)
4. `TELEGRAM_CHAT_ID` configured
5. `ALLOW_PRODUCTION_DB=false` (safety gate)

**Deliberate design:** the manual test-send (Phase 7A) requires the scheduler
to be OFF, while scheduled sends require it ON — one `.env` state can never
enable both paths simultaneously (proven by
`test_manual_and_scheduled_sends_mutually_exclusive`).

## Future activation procedure (requires explicit approval)
1. Implement the actual send loop (separate approved change — not in this train).
2. On the VPS, set the five gates above; restart.
3. `GET /api/scheduler/readiness` → `scheduled_send_gate_status: "open"`.
4. Watch the audit file (`alert_attempts_audit.jsonl`) for `kind: "scheduled"` entries.
5. Safety Matrix will show WARNING while the scheduler flag is on.
6. To deactivate: set `ENABLE_ALERT_SCHEDULER=false`, restart, verify SAFE.

## Defined jobs (data only)
| job_id | template | default interval |
|---|---|---|
| daily_system_health | system_health | 86400s |
| scout_summary | scout_summary_test | 86400s |
| dry_run_heartbeat | general_test | 300s |
