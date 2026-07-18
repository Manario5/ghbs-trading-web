import os
from typing import Dict, Any

def get_provider_readiness_status() -> Dict[str, Any]:
    smoke_tests = os.environ.get("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"
    cov_scan = os.environ.get("ENABLE_PROVIDER_COVERAGE_SCAN", "false").lower() == "true"
    live_analyze = os.environ.get("ENABLE_LIVE_ANALYZE_PREVIEW", "false").lower() == "true"
    live_scout = os.environ.get("ENABLE_LIVE_SCOUT_PREVIEW", "false").lower() == "true"
    
    twelve = os.environ.get("TWELVEDATA_API_KEY", "").strip()
    sahmk = os.environ.get("SAHMK_API_KEY", "").strip()
    tradingview = os.environ.get("TRADINGVIEW_API_KEY", "").strip()
    
    twelve_configured = bool(twelve)
    sahmk_configured = bool(sahmk)
    tradingview_configured = bool(tradingview)
    
    locked = not (smoke_tests or cov_scan or live_analyze or live_scout)
    
    state = "SAFE"
    reason = "Provider calls locked by default configuration"
    
    if smoke_tests:
        state = "WARNING"
        reason = "Market data smoke tests enabled"
    elif cov_scan:
        state = "UNSAFE"
        reason = "Provider coverage scan enabled"
    elif live_analyze or live_scout:
        state = "WARNING"
        reason = "Live preview enabled"
        
    return {
        "market_data_smoke_tests_enabled": smoke_tests,
        "provider_coverage_scan_enabled": cov_scan,
        "live_analyze_preview_enabled": live_analyze,
        "live_scout_preview_enabled": live_scout,
        "default_provider": "yfinance",
        "fallback_order": ["yfinance", "twelvedata", "sahmk", "tradingview"],
        "providers": {
            "yfinance": {
                "configured": True,
                "requires_secret": False,
                "status": "locked" if locked else "available_config_only"
            },
            "twelvedata": {
                "configured": twelve_configured,
                "requires_secret": True,
                "secret_masked": "configured" if twelve_configured else "missing"
            },
            "sahmk": {
                "configured": sahmk_configured,
                "requires_secret": True,
                "secret_masked": "configured" if sahmk_configured else "missing"
            },
            "tradingview": {
                "configured": tradingview_configured,
                "requires_secret": True,
                "secret_masked": "configured" if tradingview_configured else "missing"
            }
        },
        "provider_calls_locked": locked,
        "can_run_provider_smoke_tests": smoke_tests,
        "can_run_provider_coverage_scan": cov_scan,
        "safety_state": state,
        "locked_reason": reason
    }
