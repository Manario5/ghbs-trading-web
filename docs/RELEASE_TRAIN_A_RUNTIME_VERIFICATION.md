# Release Train A — Runtime Verification Checklist (VPS)

Perform on the VPS sandbox after deploying the branch. Access via Tailscale only
(`http://100.103.58.118:8080`). Do not modify `.env` unless a step says so.

## 1. Deploy
- [ ] `git fetch origin claude/release-train-a-alerts-telegram` into a new sandbox folder (do not overwrite the running 7a folder)
- [ ] Copy the existing `.env` from the 7a sandbox (never from git)
- [ ] Install backend deps, run backend tests: expect Train A tests green
- [ ] `npm ci && npm run build`, restart the systemd service for the new folder

## 2. Default-locked verification (no .env changes)
- [ ] `GET /api/system/safety-matrix` → `safety_state: "SAFE"`, `can_run_test_send: false`, `test_send_gate_status: "locked"`
- [ ] Login to UI → Alert Center → Telegram Readiness panel shows: TEST-SEND LOCKED badge, SAFE badge, token/chat masked as "configured", blocked reasons list the two false flags
- [ ] `POST /api/alerts/telegram/test-send` (authenticated) → `sent: false`, `network_call_made: false`
- [ ] `GET /api/alerts/telegram/status` → `last_attempt` shows the locked attempt just made; response contains no token/chat/ID values (inspect raw JSON)
- [ ] Confirm `alert_attempts_audit.jsonl` exists in the app folder and contains only masked fields
- [ ] Confirm the audit file is NOT tracked: `git status` clean of it

## 3. Templates
- [ ] `GET /api/alerts/templates` returns ≥ 7 templates
- [ ] `POST /api/alerts/templates/render` with `{"template_id":"system_health","params":{"status_line":"check"}}` renders correctly and sends nothing

## 4. Controlled test-send (only if explicitly authorized for this review)
- [ ] Set in `.env`: `ENABLE_TELEGRAM_TEST_SEND=true`, `ENABLE_TELEGRAM_SEND=true`, confirm `ENABLE_ALERT_SCHEDULER=false`; restart service
- [ ] UI panel flips to TEST-SEND OPEN with zero blocked reasons
- [ ] `POST /api/alerts/telegram/test-send` → message received in Telegram; response shows masked chat only
- [ ] Audit file gains a `test_send / sent` entry with masked target
- [ ] **Immediately** restore both flags to `false`, restart, re-verify step 2 first two checks

## 5. Sign-off
- [ ] No secrets appeared in any API response, log line, or the audit file
- [ ] Safety Matrix back to SAFE
- [ ] Record reviewed commit hash here: ____________
