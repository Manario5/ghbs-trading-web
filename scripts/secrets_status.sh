#!/bin/bash
set -euo pipefail

if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

echo "=== Secret Status ==="

check_secret() {
    local var_name="$1"
    local val="${!var_name:-}"

    if [ -z "$(echo "$val" | xargs)" ]; then
        echo "$var_name: MISSING"
    else
        echo "$var_name: CONFIGURED"
    fi
}

check_secret "ANTHROPIC_API_KEY"
check_secret "TELEGRAM_BOT_TOKEN"
check_secret "TELEGRAM_TOKEN"
check_secret "TELEGRAM_CHAT_ID"
check_secret "AUTHORIZED_USER_IDS"
check_secret "TWELVEDATA_API_KEY"
check_secret "SAHMK_API_KEY"
check_secret "TRADINGVIEW_API_KEY"

echo ""
echo "=== Telegram Alias Readiness ==="

if [ -n "$(echo "${TELEGRAM_BOT_TOKEN:-}" | xargs)" ]; then
    echo "Telegram token source: TELEGRAM_BOT_TOKEN"
elif [ -n "$(echo "${TELEGRAM_TOKEN:-}" | xargs)" ]; then
    echo "Telegram token source: TELEGRAM_TOKEN"
else
    echo "Telegram token source: MISSING"
fi

if [ -n "$(echo "${AUTHORIZED_USER_IDS:-}" | xargs)" ]; then
    AUTH_COUNT=$(echo "${AUTHORIZED_USER_IDS:-}" | tr ',' '\n' | sed '/^\s*$/d' | wc -l | xargs)
    echo "Authorized user IDs: CONFIGURED"
    echo "Authorized user IDs count: $AUTH_COUNT"
else
    echo "Authorized user IDs: MISSING"
    echo "Authorized user IDs count: 0"
fi

echo ""
echo "=== Safety Flags ==="

ALLOW_PROD="${ALLOW_PRODUCTION_DB:-false}"
DB="${DB_PATH:-tasi_ledger_test.db}"
SCHED="${ENABLE_ALERT_SCHEDULER:-false}"
LIVE_A="${ENABLE_LIVE_ANALYZE_PREVIEW:-false}"
LIVE_S="${ENABLE_LIVE_SCOUT_PREVIEW:-false}"
TG_SEND="${ENABLE_TELEGRAM_SEND:-false}"
TG_TEST="${ENABLE_TELEGRAM_TEST_SEND:-false}"

echo "ALLOW_PRODUCTION_DB=$ALLOW_PROD"
echo "DB_PATH=$DB"
echo "ENABLE_ALERT_SCHEDULER=$SCHED"
echo "ENABLE_LIVE_ANALYZE_PREVIEW=$LIVE_A"
echo "ENABLE_LIVE_SCOUT_PREVIEW=$LIVE_S"
echo "ENABLE_TELEGRAM_SEND=$TG_SEND"
echo "ENABLE_TELEGRAM_TEST_SEND=$TG_TEST"

FAILED=0

if [ "$ALLOW_PROD" = "true" ] || [ "$DB" = "tasi_ledger.db" ]; then
    echo "ERROR: Production DB flag is enabled!"
    FAILED=1
fi

if [ "$SCHED" = "true" ] || [ "$LIVE_A" = "true" ] || [ "$LIVE_S" = "true" ]; then
    echo "ERROR: A live/scheduler feature flag is enabled!"
    FAILED=1
fi

if [ "$TG_SEND" = "true" ] || [ "$TG_TEST" = "true" ]; then
    echo "ERROR: Telegram send/test flag is enabled!"
    FAILED=1
fi

if [ $FAILED -eq 1 ]; then
    exit 1
fi

exit 0
