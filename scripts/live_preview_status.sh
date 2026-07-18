#!/bin/bash
# scripts/live_preview_status.sh
# Phase 6U - Live preview manual status check

echo "=== Live Preview Status ==="

ALLOW_PROD="${ALLOW_PRODUCTION_DB:-false}"
DB="${DB_PATH:-tasi_ledger_test.db}"
ANALYZE_EN="${ENABLE_LIVE_ANALYZE_PREVIEW:-false}"
SCOUT_EN="${ENABLE_LIVE_SCOUT_PREVIEW:-false}"
SCHED="${ENABLE_ALERT_SCHEDULER:-false}"
COV_SCAN="${ENABLE_PROVIDER_COVERAGE_SCAN:-false}"

echo "ENABLE_LIVE_ANALYZE_PREVIEW=$ANALYZE_EN"
echo "ENABLE_LIVE_SCOUT_PREVIEW=$SCOUT_EN"
echo "ENABLE_ALERT_SCHEDULER=$SCHED"
echo "ENABLE_PROVIDER_COVERAGE_SCAN=$COV_SCAN"
echo "ALLOW_PRODUCTION_DB=$ALLOW_PROD"
echo "DB_PATH=$DB"

echo ""
echo "=== Endpoint Status ==="
python3 -c '
import os
import sys
sys.path.insert(0, os.path.abspath("."))
from backend.core.execution_guard import get_execution_guard_status
import json

live_analyze = os.environ.get("ENABLE_LIVE_ANALYZE_PREVIEW", "false").lower() == "true"
live_scout = os.environ.get("ENABLE_LIVE_SCOUT_PREVIEW", "false").lower() == "true"
alert_sched = os.environ.get("ENABLE_ALERT_SCHEDULER", "false").lower() == "true"
cov_scan = os.environ.get("ENABLE_PROVIDER_COVERAGE_SCAN", "false").lower() == "true"

exec_status = get_execution_guard_status()

state = "SAFE"
reason = "Safe"
if alert_sched:
    state = "UNSAFE"
    reason = "Scheduler must be disabled for manual preview"
elif cov_scan:
    state = "UNSAFE"
    reason = "Provider coverage scan must be disabled for manual preview"
elif any(exec_status.values()):
    state = "UNSAFE"
    reason = "Execution guard reported active execution capabilities"
elif not live_analyze and not live_scout:
    reason = "Locked by default configuration"

out = {
    "live_analyze_preview_enabled": live_analyze,
    "live_scout_preview_enabled": live_scout,
    "scheduler_enabled": alert_sched,
    "provider_coverage_scan_enabled": cov_scan,
    **exec_status,
    "production_db_write_enabled": False,
    "safety_state": state,
    "can_manual_analyze_preview": live_analyze and state == "SAFE",
    "can_manual_scout_preview": live_scout and state == "SAFE",
    "locked_reason": reason
}

print(json.dumps(out, indent=2))
'

echo ""
echo "Note: The preview is manual-only. It does not execute trades, send Telegram alerts, or write to production DB."
