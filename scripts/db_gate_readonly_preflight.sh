#!/bin/bash
# scripts/db_gate_readonly_preflight.sh
# Phase 6T - Read-only non-destructive preflight

echo "=== Production DB Read-Only Preflight ==="

ALLOW_PROD="${ALLOW_PRODUCTION_DB:-false}"
DB="${DB_PATH:-tasi_ledger_test.db}"
GATE_ENABLED="${ENABLE_PRODUCTION_DB_READONLY_GATE:-false}"
RO_REQ="${PRODUCTION_DB_READONLY_REQUIRED:-true}"
PROD_PATH="${PRODUCTION_DB_PATH:-}"

FAILED=0

if [ "$ALLOW_PROD" != "true" ]; then
    echo "ERROR: ALLOW_PRODUCTION_DB must be true for this preflight."
    FAILED=1
fi

if [ "$GATE_ENABLED" != "true" ]; then
    echo "ERROR: ENABLE_PRODUCTION_DB_READONLY_GATE must be true."
    FAILED=1
fi

if [ "$RO_REQ" != "true" ]; then
    echo "ERROR: PRODUCTION_DB_READONLY_REQUIRED must be true."
    FAILED=1
fi

if [ -z "$(echo "$PROD_PATH" | xargs)" ]; then
    echo "ERROR: PRODUCTION_DB_PATH must not be blank."
    FAILED=1
fi

if [ "$DB" != "tasi_ledger_test.db" ]; then
    echo "ERROR: DB_PATH must remain tasi_ledger_test.db to ensure app uses sandbox."
    FAILED=1
fi

if [ $FAILED -eq 1 ]; then
    echo "Preflight checks failed. Gate remains locked."
    exit 1
fi

echo "Preflight checks passed. Querying DB gate status..."

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

exit 0
