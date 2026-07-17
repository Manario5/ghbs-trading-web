#!/bin/bash
set -euo pipefail

echo "Running DB Gate Negative Tests..."

python3 - <<'PY'
import os
import sys
from backend.core.db_gate import get_db_gate_status


def reset_env():
    for key in [
        "ALLOW_PRODUCTION_DB",
        "DB_PATH",
        "PRODUCTION_DB_PATH",
        "ENABLE_PRODUCTION_DB_READONLY_GATE",
        "PRODUCTION_DB_READONLY_REQUIRED",
    ]:
        os.environ.pop(key, None)


def check(condition, msg):
    if not condition:
        print(f"FAILED: {msg}")
        sys.exit(1)


reset_env()
status = get_db_gate_status()
check(status["gate_locked"] is True, "Gate should be locked by default")

reset_env()
os.environ["ALLOW_PRODUCTION_DB"] = "true"
os.environ["ENABLE_PRODUCTION_DB_READONLY_GATE"] = "true"
os.environ["PRODUCTION_DB_READONLY_REQUIRED"] = "true"
os.environ["PRODUCTION_DB_PATH"] = "   "
os.environ["DB_PATH"] = "tasi_ledger_test.db"
status = get_db_gate_status()
check(status["gate_locked"] is True, "Blank production DB path should keep gate locked")

reset_env()
os.environ["ALLOW_PRODUCTION_DB"] = "true"
os.environ["ENABLE_PRODUCTION_DB_READONLY_GATE"] = "true"
os.environ["PRODUCTION_DB_READONLY_REQUIRED"] = "false"
os.environ["PRODUCTION_DB_PATH"] = "some_path.db"
os.environ["DB_PATH"] = "tasi_ledger_test.db"
status = get_db_gate_status()
check(status["gate_locked"] is True, "Read-only required false should lock gate")
check(status["error_category"] == "UNSAFE_READONLY_NOT_REQUIRED", "Should report unsafe readonly not required")

reset_env()
os.environ["ALLOW_PRODUCTION_DB"] = "true"
os.environ["ENABLE_PRODUCTION_DB_READONLY_GATE"] = "true"
os.environ["PRODUCTION_DB_READONLY_REQUIRED"] = "true"
os.environ["PRODUCTION_DB_PATH"] = "some_path.db"
os.environ["DB_PATH"] = "tasi_ledger.db"
status = get_db_gate_status()
check(status["gate_locked"] is True, "DB_PATH=tasi_ledger.db must keep gate locked")
check(status["error_category"] == "UNSAFE_DB_PATH_NOT_SANDBOX", "Should report unsafe DB_PATH not sandbox")

print("All DB gate negative checks passed.")
PY

echo "DB Gate Negative Tests passed successfully."
