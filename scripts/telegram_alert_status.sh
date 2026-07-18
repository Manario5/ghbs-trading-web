#!/bin/bash
set -euo pipefail

if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

mask_status() {
    local val="${1:-}"
    if [ -z "$(echo "$val" | xargs)" ]; then
        echo "MISSING"
    else
        echo "CONFIGURED"
    fi
}

echo "=== Telegram Alert Status ==="
echo "TELEGRAM_BOT_TOKEN=$(mask_status "${TELEGRAM_BOT_TOKEN:-}")"
echo "TELEGRAM_CHAT_ID=$(mask_status "${TELEGRAM_CHAT_ID:-}")"
echo "ENABLE_TELEGRAM_DRY_RUN=${ENABLE_TELEGRAM_DRY_RUN:-true}"
echo "ENABLE_TELEGRAM_SEND=${ENABLE_TELEGRAM_SEND:-false}"
echo "ENABLE_TELEGRAM_TEST_SEND=${ENABLE_TELEGRAM_TEST_SEND:-false}"
echo "ENABLE_ALERT_SCHEDULER=${ENABLE_ALERT_SCHEDULER:-false}"

echo ""
echo "=== Endpoint Status ==="
if curl -fsS http://127.0.0.1:8000/api/system/telegram-alert-status >/tmp/telegram_alert_status.json 2>/dev/null; then
    python3 -m json.tool /tmp/telegram_alert_status.json
else
    echo "Backend not reachable on 127.0.0.1:8000; endpoint check skipped."
fi
