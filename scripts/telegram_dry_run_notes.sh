#!/bin/bash
set -euo pipefail

cat <<'TXT'
Phase 6X Telegram / Secret Alias Notes

This phase is configuration-readiness only.

Supported:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_TOKEN as alias if TELEGRAM_BOT_TOKEN is missing
- TELEGRAM_CHAT_ID
- AUTHORIZED_USER_IDS
- ANTHROPIC_API_KEY readiness

Safety:
- Do not paste real secrets into chat.
- Do not commit .env to GitHub.
- Status scripts print CONFIGURED or MISSING only.
- AUTHORIZED_USER_IDS prints only a count, not values.
- Telegram sending remains disabled.
- Telegram network calls remain locked.
- Anthropic calls are not made in this phase.

Later controlled phases may use the real values from VPS .env only.
TXT
