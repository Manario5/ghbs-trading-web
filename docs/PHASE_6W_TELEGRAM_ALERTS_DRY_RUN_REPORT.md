# Phase 6W — Telegram Alerts Bot Dry-Run Foundation

## Purpose
Phase 6W adds Telegram alert readiness and dry-run preview capability without sending any Telegram messages.

## Files Added or Changed
- backend/core/telegram_readiness.py
- backend/api/system.py
- backend/api/alerts.py
- backend/tests/test_phase6w.py
- scripts/telegram_alert_status.sh
- scripts/telegram_negative_tests.sh
- scripts/telegram_dry_run_notes.sh
- scripts/validate_release.sh

## Safety Guarantees
- No real Telegram messages are sent.
- Telegram Bot API is not called.
- Telegram network calls are locked.
- Telegram secrets are masked only.
- Alert scheduler remains disabled by default.
- Production DB remains locked.
- Provider calls remain locked.
- Broker and trade execution remain disabled.

## Default Environment
ENABLE_TELEGRAM_DRY_RUN=true
ENABLE_TELEGRAM_SEND=false
ENABLE_TELEGRAM_TEST_SEND=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ENABLE_ALERT_SCHEDULER=false

## Endpoints
- GET /api/system/telegram-alert-status
- POST /api/alerts/telegram/dry-run-preview

The dry-run preview returns dry_run=true, would_send=false, execution_allowed=false, and telegram_network_calls_locked=true.

## Remaining Later Work
- Controlled manual Telegram test-send gate.
- Scheduler dry-run alert generation.
- Real Telegram sending only after explicit approval in a later phase.
