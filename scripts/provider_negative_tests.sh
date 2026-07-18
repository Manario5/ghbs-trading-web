#!/bin/bash
# scripts/provider_negative_tests.sh
# Phase 6V - Provider negative testing

echo "Running Provider Negative Tests..."

FAILED=0

cat << 'EOF' > test_provider_negative.py
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.core.provider_readiness import get_provider_readiness_status

def check(condition, msg):
    if not condition:
        print(f"FAILED: {msg}")
        sys.exit(1)

# 1. Default locked state
os.environ.clear()
data = get_provider_readiness_status()
check(data["provider_calls_locked"] == True, "Default provider_calls_locked should be True")
check(data["safety_state"] == "SAFE", "Default safety state should be SAFE")
check("locked" in data["providers"]["yfinance"]["status"], "yfinance status should be locked by default")

# 2. ENABLE_MARKET_DATA_SMOKE_TESTS=false prevents smoke execution
os.environ["ENABLE_MARKET_DATA_SMOKE_TESTS"] = "false"
data = get_provider_readiness_status()
check(data["can_run_provider_smoke_tests"] == False, "smoke tests should be false")
check(data["provider_calls_locked"] == True, "calls should be locked")

# 3. Missing API keys reported missing and masked
os.environ.clear()
data = get_provider_readiness_status()
check(data["providers"]["twelvedata"]["configured"] == False, "twelvedata configured should be false")
check(data["providers"]["twelvedata"]["secret_masked"] == "missing", "twelvedata secret should be missing")
check(data["providers"]["sahmk"]["configured"] == False, "sahmk configured should be false")
check(data["providers"]["tradingview"]["configured"] == False, "tradingview configured should be false")

# 4. No full secrets in output
os.environ["TWELVEDATA_API_KEY"] = "super-secret-key"
data = get_provider_readiness_status()
check(data["providers"]["twelvedata"]["configured"] == True, "twelvedata configured should be true")
check(data["providers"]["twelvedata"]["secret_masked"] == "configured", "twelvedata secret should be configured (masked)")
check("super-secret-key" not in str(data), "full secret should NOT be in JSON output")

print("All Provider negative checks passed.")
sys.exit(0)
EOF

python3 test_provider_negative.py
if [ $? -ne 0 ]; then
    FAILED=1
fi
rm test_provider_negative.py

if [ $FAILED -ne 0 ]; then
    echo "ERROR: Provider Negative Tests failed."
    exit 1
fi

echo "Provider Negative Tests passed successfully."
exit 0
