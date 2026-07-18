# Release Train A — Rollback Checklist

Use if the Train A deployment misbehaves on the VPS. The train adds only
additive backend modules, three authenticated read/preview endpoints, audit
recording, and a UI panel — no schema changes, no data migrations, so rollback
is a pure redeploy of the previous tag.

## Fast rollback (return to phase-7a-approved runtime)
1. [ ] Point the systemd service back at the previous sandbox folder (`/root/ghbs-trading-web-sandbox-7a`) and restart
2. [ ] Verify `GET /api/system/safety-matrix` → `safety_state: "SAFE"`
3. [ ] Verify UI loads (Alert Center will simply lack the new panel)

## Full rollback (rebuild from tag)
1. [ ] `git checkout phase-7a-approved` into a fresh folder
2. [ ] Copy `.env` from the previous runtime folder (never from git); confirm all send flags are `false`
3. [ ] Reinstall deps, run backend tests, `npm run build`, point systemd at the folder, restart

## Cleanup
- [ ] The Train A audit file (`alert_attempts_audit.jsonl`) contains only masked data; it may be kept for reference or deleted — either is safe
- [ ] No env vars need removal: `ALERT_AUDIT_FILE` is optional and ignored by the 7a code
- [ ] Confirm no `.env` flag was left enabled: `ENABLE_TELEGRAM_SEND=false`, `ENABLE_TELEGRAM_TEST_SEND=false`, `ENABLE_ALERT_SCHEDULER=false`

## Post-rollback verification
- [ ] Safety Matrix SAFE
- [ ] Login works, dashboard loads
- [ ] `POST /api/alerts/telegram/test-send` returns locked
- [ ] Note failure reason and attach findings to the Train A review thread before re-attempting
