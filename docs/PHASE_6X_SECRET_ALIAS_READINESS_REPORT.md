# Phase 6X — Secret Alias Support + Safe Configuration Readiness

## Purpose
Phase 6X adds safe readiness support for secret aliases and masked authorized user configuration.
This phase does not use real secrets, does not call Anthropic, and does not send Telegram messages.

## Supported Variables
- ANTHROPIC_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_TOKEN as alias for TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- AUTHORIZED_USER_IDS

## Safety Guarantees
- Secrets are reported only as configured or missing.
- TELEGRAM_TOKEN is accepted as an alias only when TELEGRAM_BOT_TOKEN is missing.
- TELEGRAM_BOT_TOKEN takes precedence if both token variables exist.
- AUTHORIZED_USER_IDS are never printed; only count is shown.
- Telegram network calls remain locked.
- Telegram send and test-send remain false.
- Alert scheduler remains disabled.
- Production DB remains locked.

## Files Changed
- backend/core/telegram_readiness.py
- backend/core/secrets.py
- backend/api/system.py
- backend/tests/test_phase6x.py
- scripts/secrets_status.sh
- scripts/telegram_alert_status.sh
- scripts/telegram_negative_tests.sh
- .env.example

## Remaining Later Work
- Enter real secrets on the VPS only after explicit approval.
- Add controlled Telegram manual test-send in a later phase.
- Add controlled Anthropic integration in a later phase.
