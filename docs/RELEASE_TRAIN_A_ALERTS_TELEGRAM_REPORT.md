# Release Train A — Alerts & Telegram Completion

**Date:** 2026-07-18
**Branch:** claude/release-train-a-alerts-telegram
**Base:** main @ 5a4972e (phase-7a-approved)
**Status:** Implementation complete — pending VPS review. No merge, no tag.

---

## Scope Delivered

### 1. Review of existing Telegram stack (no changes needed to core gate logic)
- `backend/core/telegram_readiness.py` — readiness + status (Phase 6W/6X/7A) ✔ reviewed, unchanged
- `backend/core/telegram_sender.py` — five-gate manual sender (Phase 7A) ✔ reviewed, unchanged
- `POST /api/alerts/telegram/dry-run-preview` ✔ reviewed, now also records an audit entry
- `POST /api/alerts/telegram/test-send` ✔ reviewed, now also records audit entries (locked and allowed paths)

The Phase 7A five-gate model was found sound and is reused untouched:
`ENABLE_TELEGRAM_TEST_SEND=true` + `ENABLE_TELEGRAM_SEND=true` + `ENABLE_ALERT_SCHEDULER=false` + token + chat ID.

### 2. Alert template registry — `backend/core/alert_templates.py` (new)
- Test templates: `general_test`, `manual_test_send`, `scout_summary_test`
- Future system templates (defined, delivery NOT implemented): `setup_detected`, `tp_hit`, `stop_hit`, `system_health`
- `render_template()` is exception-free: unknown ids return a structured error, missing params stay as visible `{placeholder}` text
- No template references tokens, chat IDs, or API keys (enforced by test)

### 3. File-based alert attempt audit layer — `backend/core/alert_audit.py` (new)
- Append-only JSONL file (`ALERT_AUDIT_FILE`, default `alert_attempts_audit.jsonl`, gitignored)
- Records every dry-run preview and test-send attempt: kind, outcome (locked/sent/failed), gate status, blocked reasons, masked target
- **Field allowlist** — anything outside the allowlist (e.g. a token accidentally passed in) is dropped before writing (enforced by test)
- Write failures never break the calling endpoint; corrupt lines are skipped on read

### 4. New API endpoints (all require authentication)
| Endpoint | Purpose |
|---|---|
| `GET /api/alerts/telegram/status` | Unified readiness + gates + blocked reasons + last attempt + 10 recent attempts |
| `GET /api/alerts/templates` | List template registry |
| `POST /api/alerts/templates/render` | Server-side render preview (never sends) |

### 5. UI visibility — `src/components/TelegramStatusPanel.tsx` (new), mounted at top of AlertCenter
- Telegram readiness (token source, chat ID, authorized IDs — masked values only)
- Test-send gate status badge (LOCKED/OPEN) and safety state badge (SAFE/WARNING)
- Blocked reasons list (exact gate failures)
- Send/test/scheduler flag values
- Last dry-run/test-send attempt (time, kind, outcome, network call, masked target)

### 6–12. Safety posture (unchanged)
- All sending locked by default; `.env.example` keeps all flags `false`
- Scheduler untouched; no automatic sends
- No production DB, no live trading, no strategy changes, no public exposure
- No secrets printed, logged, committed, or documented

---

## Files Changed

| File | Change |
|---|---|
| `docs/REMAINING_WORK_ACCELERATION_PLAN.md` | new — release train roadmap |
| `backend/core/alert_templates.py` | new — template registry |
| `backend/core/alert_audit.py` | new — JSONL audit layer |
| `backend/api/alerts.py` | new endpoints + audit recording on dry-run/test-send |
| `src/components/TelegramStatusPanel.tsx` | new — readiness/gates UI panel |
| `src/pages/AlertCenter.tsx` | mounts the panel |
| `.env.example` | `ALERT_AUDIT_FILE` documented |
| `.gitignore` | ignore runtime audit file |
| `backend/tests/test_release_train_a.py` | new — 19 tests |
| `docs/RELEASE_TRAIN_A_ALERTS_TELEGRAM_REPORT.md` | this report |
| `docs/RELEASE_TRAIN_A_RUNTIME_VERIFICATION.md` | verification checklist |
| `docs/RELEASE_TRAIN_A_ROLLBACK.md` | rollback checklist |

Frozen modules (`tasi_engine_v7_2_1.py`, classifier/regime/sizes/chandelier/executor/universe) — **not touched**.

---

## Validation Results

| Check | Result |
|---|---|
| Focused tests (`test_release_train_a.py`) | 19/19 pass |
| Full backend sync tests | 69 pass, 0 new failures (12 pre-existing async failures unchanged — missing `pytest-asyncio`, tracked for Train B) |
| Frontend build (`vite build`) | pass |
| Secret scan on changed files | clean (only clearly-fake test literals) |
| Negative tests (auth required, locked default, missing-file audit, corrupt lines, unknown template, secret-field stripping) | all pass |
| Safety matrix default | SAFE, `can_run_test_send: false`, gate `locked` |

---

*This report contains no secret values.*
