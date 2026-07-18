#!/bin/bash
# scripts/db_gate_negative_tests.sh
# Phase 6T - DB Gate Negative Testing (No mutations)

echo "Running DB Gate Negative Tests..."

FAILED=0

# Helper to run curl with specific env vars (actually we can't easily inject env vars into a running API process)
# We will use python to directly test the db_gate module safely.

cat << 'EOF' > test_db_gate_negative.py
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.core.db_gate import get_db_gate_status

def check(condition, msg):
    if not condition:
        print(f"FAILED: {msg}")
        sys.exit(1)

# 1. Default state is locked
os.environ.clear()
status = get_db_gate_status()
check(status["gate_locked"] == True, "Gate should be locked by default")

# 2. Blank PRODUCTION_DB_PATH is locked
os.environ["ALLOW_PRODUCTION_DB"] = "true"
os.environ["ENABLE_PRODUCTION_DB_READONLY_GATE"] = "true"
os.environ["PRODUCTION_DB_READONLY_REQUIRED"] = "true"
os.environ["PRODUCTION_DB_PATH"] = "   "
status = get_db_gate_status()
check(status["gate_locked"] == True, "Blank DB path should keep gate locked")

# 3. PRODUCTION_DB_READONLY_REQUIRED=false is unsafe/locked
os.environ["PRODUCTION_DB_PATH"] = "some_path.db"
os.environ["PRODUCTION_DB_READONLY_REQUIRED"] = "false"
status = get_db_gate_status()
check(status["gate_locked"] == True, "Read-only required = false should lock gate")
check(status["error_category"] == "UNSAFE_READONLY_NOT_REQUIRED", "Should report unsafe readonly not required")

print("All DB gate negative checks passed.")
sys.exit(0)
EOF

python3 test_db_gate_negative.py
if [ $? -ne 0 ]; then
    FAILED=1
fi
rm test_db_gate_negative.py

if [ $FAILED -ne 0 ]; then
    echo "ERROR: DB Gate Negative Tests failed."
    exit 1
fi

echo "DB Gate Negative Tests passed successfully."
exit 0
