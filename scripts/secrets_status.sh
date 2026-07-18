#!/bin/bash
set -euo pipefail

if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

status_var() {
    local name="$1"
    local val="${!name:-}"
    if [ -z "$(echo "$val" | xargs)" ]; then
        echo "$name: MISSING"
    else
        echo "$name: CONFIGURED"
    fi
}

echo "=== Secret Status ==="
status_var ANTHROPIC_API_KEY
status_var TELEGRAM_BOT_TOKEN
status_var TELEGRAM_CHAT_ID
status_var TWELVEDATA_API_KEY
status_var SAHMK_API_KEY
status_var TRADINGVIEW_API_KEY

echo ""
echo "=== Safety Flags ==="
echo "ALLOW_PRODUCTION_DB=${ALLOW_PRODUCTION_DB:-}"
echo "DB_PATH=${DB_PATH:-}"
echo "ENABLE_ALERT_SCHEDULER=${ENABLE_ALERT_SCHEDULER:-}"
echo "ENABLE_PROVIDER_COVERAGE_SCAN=${ENABLE_PROVIDER_COVERAGE_SCAN:-}"
echo "ENABLE_LIVE_ANALYZE_PREVIEW=${ENABLE_LIVE_ANALYZE_PREVIEW:-}"
echo "ENABLE_LIVE_SCOUT_PREVIEW=${ENABLE_LIVE_SCOUT_PREVIEW:-}"
echo "ENABLE_PRODUCTION_DB_READONLY_GATE=${ENABLE_PRODUCTION_DB_READONLY_GATE:-}"
echo "PRODUCTION_DB_READONLY_REQUIRED=${PRODUCTION_DB_READONLY_REQUIRED:-}"

if [ -z "$(echo "${PRODUCTION_DB_PATH:-}" | xargs)" ]; then
    echo "PRODUCTION_DB_PATH=MISSING"
else
    echo "PRODUCTION_DB_PATH=CONFIGURED"
fi
