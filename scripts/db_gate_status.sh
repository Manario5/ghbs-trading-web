#!/bin/bash
# scripts/db_gate_status.sh
# Phase 6T - Read-only DB gate status check

echo "=== Production DB Read-Only Gate Status ==="

ALLOW_PROD="${ALLOW_PRODUCTION_DB:-false}"
DB="${DB_PATH:-tasi_ledger_test.db}"
GATE_ENABLED="${ENABLE_PRODUCTION_DB_READONLY_GATE:-false}"
RO_REQ="${PRODUCTION_DB_READONLY_REQUIRED:-true}"

if [ -z "$(echo "${PRODUCTION_DB_PATH:-}" | xargs)" ]; then
    PATH_CONFIGURED="MISSING"
else
    PATH_CONFIGURED="CONFIGURED"
    BASENAME=$(basename "$PRODUCTION_DB_PATH")
fi

echo "ALLOW_PRODUCTION_DB=$ALLOW_PROD"
echo "DB_PATH=$DB"
echo "ENABLE_PRODUCTION_DB_READONLY_GATE=$GATE_ENABLED"
echo "PRODUCTION_DB_READONLY_REQUIRED=$RO_REQ"
echo "PRODUCTION_DB_PATH=$PATH_CONFIGURED"

if [ "$PATH_CONFIGURED" = "CONFIGURED" ]; then
    echo "PRODUCTION_DB_BASENAME=$BASENAME"
fi

echo ""
echo "=== Production DB Path Status ==="
python3 -c '
import os
import sys
sys.path.insert(0, os.path.abspath("."))
try:
    from backend.core.db_gate import get_db_gate_status
    import json
    print(json.dumps(get_db_gate_status(), indent=2))
except Exception as e:
    print(f"Failed to load status natively: {e}")
'

echo ""
echo "Note: The gate prevents DB mutability and only acts as a read-only check."
