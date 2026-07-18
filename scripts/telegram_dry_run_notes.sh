#!/bin/bash
set -euo pipefail

cat <<'TXT'
Phase 6W Telegram Dry-Run Notes

This phase is dry-run only.

Allowed:
- View Telegram readiness status.
- Generate local dry-run preview payloads.
- Verify token/chat id are configured or missing using masked status only.

Not allowed in Phase 6W:
- Real Telegram Bot API calls.
- Real Telegram sending.
- Scheduler-triggered alerts.
- Production DB writes.
- Broker/order execution.

Later controlled phases may add a manual test-send gate, but this script does not enable anything.
TXT
