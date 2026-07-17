#!/bin/bash
set -euo pipefail

echo "=== Production DB Read-Only Gate Status ==="

if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

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
echo "=== Local Module Status ==="
python3 - <<'PY'
import json
from backend.core.db_gate import get_db_gate_status
print(json.dumps(get_db_gate_status(), indent=2))
PY

echo ""
echo "=== API Status if backend is running ==="
if curl -fsS http://127.0.0.1:8000/api/system/db-gate-status >/tmp/db_gate_status.json 2>/dev/null; then
    cat /tmp/db_gate_status.json
    echo
else
    echo "Backend API not reachable on 127.0.0.1:8000. Local module status above is still valid."
fi

rm -f /tmp/db_gate_status.json
echo ""
echo "Note: This gate checks read-only access only. It does not switch the app database."
