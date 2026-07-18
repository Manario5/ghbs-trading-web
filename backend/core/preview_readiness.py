"""
Live Preview / Scout / Analyze readiness — Release Train D.

Config-only gate evaluation for the live preview features. The preview
endpoints themselves (backend/api/live_preview.py) already enforce their env
gates; this module gives the UI and the ops status page a single view of why
preview is or is not available. No network calls, no engine calls.
"""
import os
from typing import Any, Dict, List


def _env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def get_preview_readiness() -> Dict[str, Any]:
    analyze_flag = _env_bool("ENABLE_LIVE_ANALYZE_PREVIEW")
    scout_flag = _env_bool("ENABLE_LIVE_SCOUT_PREVIEW")
    md_flag = _env_bool("ENABLE_MARKET_DATA_SMOKE_TESTS")
    ohlcv_flag = _env_bool("ENABLE_OHLCV_DIAGNOSTICS")
    allow_prod = _env_bool("ALLOW_PRODUCTION_DB")
    db_path = os.environ.get("DB_PATH", "tasi_ledger_test.db")

    analyze_blockers: List[str] = []
    if not analyze_flag:
        analyze_blockers.append("ENABLE_LIVE_ANALYZE_PREVIEW is false")
    if not md_flag:
        analyze_blockers.append("ENABLE_MARKET_DATA_SMOKE_TESTS is false")
    if not ohlcv_flag:
        analyze_blockers.append("ENABLE_OHLCV_DIAGNOSTICS is false")

    scout_blockers: List[str] = []
    if not scout_flag:
        scout_blockers.append("ENABLE_LIVE_SCOUT_PREVIEW is false")
    if not md_flag:
        scout_blockers.append("ENABLE_MARKET_DATA_SMOKE_TESTS is false")
    if not ohlcv_flag:
        scout_blockers.append("ENABLE_OHLCV_DIAGNOSTICS is false")

    safety_blockers: List[str] = []
    if allow_prod:
        safety_blockers.append("ALLOW_PRODUCTION_DB must remain false for previews")
    if "tasi_ledger_test.db" not in db_path:
        safety_blockers.append("DB_PATH must point at the test ledger")

    return {
        "analyze_preview_enabled": analyze_flag,
        "scout_preview_enabled": scout_flag,
        "market_data_smoke_tests_enabled": md_flag,
        "ohlcv_diagnostics_enabled": ohlcv_flag,
        "can_run_analyze_preview": not analyze_blockers and not safety_blockers,
        "can_run_scout_preview": not scout_blockers and not safety_blockers,
        "analyze_blockers": analyze_blockers,
        "scout_blockers": scout_blockers,
        "safety_blockers": safety_blockers,
        "writes_production_db": False,
        "executes_trades": False,
        "strategy_engine": "frozen (tasi_engine V7.2.1 logic, read-only use)",
        "safety_state": "SAFE" if not (analyze_flag or scout_flag) else "WARNING",
    }


def build_sample_preview() -> Dict[str, Any]:
    """
    Static sample of the preview output format. No engine execution, no
    market data, no network. Lets the UI and reviewers see the result shape
    while everything is locked.
    """
    return {
        "sample": True,
        "dry_run": True,
        "note": "Static format sample only — no engine run, no market data fetched.",
        "result_format": {
            "ticker": "0000.SR",
            "provider_used": "yfinance",
            "bars_used": 180,
            "regime": "SAMPLE_REGIME",
            "setup_type": "SAMPLE_SETUP",
            "signal": "WATCH",
            "entry_zone": {"low": 0.0, "high": 0.0},
            "stop_level": 0.0,
            "targets": [0.0, 0.0],
            "position_size_pct": 0.0,
            "chandelier_level": 0.0,
            "generated_at": "<UTC ISO timestamp>",
        },
    }
