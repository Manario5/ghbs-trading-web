#!/bin/bash
# scripts/secrets_status.sh
# Phase 6S - Safe secret checking only.

echo "=== Secret Status ==="

check_secret() {
    local var_name="$1"
    local val="${!var_name}"
    
    if [ -z "$(echo "$val" | xargs)" ]; then # Strip whitespace to check empty
        echo "$var_name: MISSING"
    else
        echo "$var_name: CONFIGURED"
    fi
}

check_secret "ANTHROPIC_API_KEY"
check_secret "TELEGRAM_BOT_TOKEN"
check_secret "TELEGRAM_CHAT_ID"
check_secret "TWELVEDATA_API_KEY"
check_secret "SAHMK_API_KEY"
check_secret "TRADINGVIEW_API_KEY"

echo ""
echo "=== Safety Flags ==="

ALLOW_PROD="${ALLOW_PRODUCTION_DB:-false}"
DB="${DB_PATH:-tasi_ledger_test.db}"
SCHED="${ENABLE_ALERT_SCHEDULER:-false}"
LIVE_A="${ENABLE_LIVE_ANALYZE_PREVIEW:-false}"
LIVE_S="${ENABLE_LIVE_SCOUT_PREVIEW:-false}"

echo "ALLOW_PRODUCTION_DB=$ALLOW_PROD"
echo "DB_PATH=$DB"
echo "ENABLE_ALERT_SCHEDULER=$SCHED"
echo "ENABLE_LIVE_ANALYZE_PREVIEW=$LIVE_A"
echo "ENABLE_LIVE_SCOUT_PREVIEW=$LIVE_S"

FAILED=0

if [ "$ALLOW_PROD" = "true" ] || [ "$DB" = "tasi_ledger.db" ]; then
    echo "ERROR: Production DB flag is enabled!"
    FAILED=1
fi

if [ "$SCHED" = "true" ] || [ "$LIVE_A" = "true" ] || [ "$LIVE_S" = "true" ]; then
    echo "ERROR: A live/scheduler feature flag is enabled!"
    FAILED=1
fi

if [ $FAILED -eq 1 ]; then
    exit 1
fi

exit 0
