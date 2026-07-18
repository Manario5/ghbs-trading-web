#!/bin/bash
# scripts/provider_readiness_status.sh
# Phase 6V - Market data provider readiness status check

echo "=== Provider Readiness Status ==="

SMOKE="${ENABLE_MARKET_DATA_SMOKE_TESTS:-false}"
COV_SCAN="${ENABLE_PROVIDER_COVERAGE_SCAN:-false}"
LIVE_ANALYZE="${ENABLE_LIVE_ANALYZE_PREVIEW:-false}"
LIVE_SCOUT="${ENABLE_LIVE_SCOUT_PREVIEW:-false}"

echo "ENABLE_MARKET_DATA_SMOKE_TESTS=$SMOKE"
echo "ENABLE_PROVIDER_COVERAGE_SCAN=$COV_SCAN"
echo "ENABLE_LIVE_ANALYZE_PREVIEW=$LIVE_ANALYZE"
echo "ENABLE_LIVE_SCOUT_PREVIEW=$LIVE_SCOUT"

echo ""
echo "=== Endpoint Status ==="
python3 -c '
import os
import sys
sys.path.insert(0, os.path.abspath("."))
try:
    from backend.core.provider_readiness import get_provider_readiness_status
    import json
    print(json.dumps(get_provider_readiness_status(), indent=2))
except Exception as e:
    print(f"Failed to load status natively: {e}")
'
