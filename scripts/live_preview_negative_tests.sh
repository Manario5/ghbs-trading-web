#!/bin/bash
# scripts/live_preview_negative_tests.sh
# Phase 6U - Live Preview Negative Testing

echo "Running Live Preview Negative Tests..."

FAILED=0

cat << 'EOF' > test_live_preview_negative.py
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.execution_guard import assert_no_execution_allowed, ExecutionNotAllowedError

def check(condition, msg):
    if not condition:
        print(f"FAILED: {msg}")
        sys.exit(1)

# 1. Default locked state
os.environ.clear()
with TestClient(app) as client:
    resp = client.get("/api/system/live-preview-status")
    data = resp.json()
    check(data["can_manual_analyze_preview"] == False, "Default analyze preview should be locked")
    check(data["can_manual_scout_preview"] == False, "Default scout preview should be locked")
    check(data["safety_state"] == "SAFE", "Default safety state should be SAFE")

# 2. Scheduler enabled makes status unsafe/blocked
os.environ["ENABLE_LIVE_ANALYZE_PREVIEW"] = "true"
os.environ["ENABLE_ALERT_SCHEDULER"] = "true"
with TestClient(app) as client:
    resp = client.get("/api/system/live-preview-status")
    data = resp.json()
    check(data["safety_state"] == "UNSAFE", "Scheduler enabled should be UNSAFE")
    check(data["can_manual_analyze_preview"] == False, "Scheduler enabled should block analyze preview")

# 3. Provider coverage scan enabled makes status unsafe/blocked
os.environ["ENABLE_ALERT_SCHEDULER"] = "false"
os.environ["ENABLE_PROVIDER_COVERAGE_SCAN"] = "true"
with TestClient(app) as client:
    resp = client.get("/api/system/live-preview-status")
    data = resp.json()
    check(data["safety_state"] == "UNSAFE", "Provider coverage enabled should be UNSAFE")
    check(data["can_manual_analyze_preview"] == False, "Provider coverage enabled should block analyze preview")

# 4. ALLOW_PRODUCTION_DB=true with unsafe DB_PATH is unsafe
os.environ.clear()
os.environ["ALLOW_PRODUCTION_DB"] = "true"
os.environ["DB_PATH"] = "some_prod.db"
with TestClient(app) as client:
    resp = client.get("/api/system/safety-matrix")
    data = resp.json()
    check(data["safety_state"] == "UNSAFE", "Production DB access with unsafe DB_PATH should be UNSAFE")

# 5. Execution guard blocks
blocked = False
try:
    assert_no_execution_allowed()
except ExecutionNotAllowedError:
    blocked = True
check(blocked, "Execution guard did not block execution")

print("All Live Preview negative checks passed.")
sys.exit(0)
EOF

python3 test_live_preview_negative.py
if [ $? -ne 0 ]; then
    FAILED=1
fi
rm test_live_preview_negative.py

if [ $FAILED -ne 0 ]; then
    echo "ERROR: Live Preview Negative Tests failed."
    exit 1
fi

echo "Live Preview Negative Tests passed successfully."
exit 0
