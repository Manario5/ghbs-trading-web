"""
Operating-mode model — Private Live Command Center.

Derives a business-friendly operating mode from the environment gates and the
canonical safety state. This module is read-only: it never enables anything,
never calls providers, and never writes to any database.

Modes:
- PRIVATE_LIVE       : live market data / previews / manual Telegram enabled,
                       no scheduled automation, read-only, no execution.
- AUTOMATED_ALERTS   : the alert scheduler is intentionally enabled.
- LOCKED_MAINTENANCE : all external/live actions disabled.
- RESTRICTED         : a dangerous condition is present (prod DB write path or
                       active execution) — should never occur in this app.

Hard invariants surfaced to operators (always true here):
- Trade/broker execution is impossible.
- Production DB writes are impossible.
- Live previews are read-only.
"""
import os
from typing import Any, Dict

from backend.core.safety_state import compute_safety_state


def _bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def get_operating_mode(db_path: str, exec_active: bool) -> Dict[str, Any]:
    derived = compute_safety_state(db_path, exec_active)

    market_data = _bool("ENABLE_MARKET_DATA_SMOKE_TESTS")
    api_smoke = _bool("ENABLE_API_SMOKE_TESTS")
    ohlcv = _bool("ENABLE_OHLCV_DIAGNOSTICS")
    coverage = _bool("ENABLE_PROVIDER_COVERAGE_SCAN")
    live_analyze = _bool("ENABLE_LIVE_ANALYZE_PREVIEW")
    live_scout = _bool("ENABLE_LIVE_SCOUT_PREVIEW")
    scheduler = _bool("ENABLE_ALERT_SCHEDULER")
    scheduler_dry_run_only = _bool("ALERT_SCHEDULER_DRY_RUN_ONLY", "true")
    tg_send = _bool("ENABLE_TELEGRAM_SEND")
    tg_test = _bool("ENABLE_TELEGRAM_TEST_SEND")
    tg_dry_run = _bool("ENABLE_TELEGRAM_DRY_RUN", "true")

    anthropic_ready = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())

    any_live_gate = any([
        market_data, api_smoke, ohlcv, coverage,
        live_analyze, live_scout, tg_send, tg_test,
    ])

    if derived["unsafe_reasons"]:
        mode = "RESTRICTED"
        mode_label = "RESTRICTED"
        description = "A dangerous capability is enabled. Review immediately."
    elif scheduler:
        mode = "AUTOMATED_ALERTS"
        mode_label = "AUTOMATED ALERTS"
        description = (
            "Alert scheduler is enabled. Telegram sending is active. Manual alerts "
            "and test-send are available. Trade execution, broker execution, "
            "production DB write, and public exposure remain impossible."
        )
    elif any_live_gate:
        mode = "PRIVATE_LIVE"
        mode_label = "PRIVATE LIVE"
        description = (
            "Live market data and read-only previews are active. Manual Telegram "
            "sending may be active. Scheduler is not running unless enabled."
        )
    else:
        mode = "LOCKED_MAINTENANCE"
        mode_label = "LOCKED / MAINTENANCE"
        description = "External/live gates are locked."

    telegram_sending_active = tg_send or tg_test

    return {
        "mode": mode,
        "mode_label": mode_label,
        "description": description,
        "safety_state": derived["safety_state"],
        "warning_reasons": derived["warning_reasons"],
        "unsafe_reasons": derived["unsafe_reasons"],
        "capabilities": {
            "market_data_provider_usage": market_data,
            "quote_tests": api_smoke or market_data,
            "ohlcv_diagnostics": ohlcv,
            "provider_readiness": True,   # readiness view is always available
            "provider_coverage_scan": coverage,
            "live_analyze_preview": live_analyze,
            "live_scout_preview": live_scout,
            "anthropic_ready": anthropic_ready,
            "manual_telegram_alerts": True,   # manual composer always available (send still gated)
            "telegram_test_send": tg_test,
            "telegram_dry_run": tg_dry_run,
            "alert_delivery_log": True,
            "scheduler_readiness_panel": True,
        },
        "automation": {
            "scheduler_enabled": scheduler,
            "scheduler_dry_run_only": scheduler_dry_run_only,
        },
        "telegram_sending_active": telegram_sending_active,
        "live_preview_read_only": True,
        "production_db_write_possible": False,
        "trade_execution_possible": False,
        "broker_execution_possible": False,
        "public_exposure": "blocked_by_network_policy (not enforced in app layer)",
        "blocked": {
            "trade_execution": True,
            "broker_execution": True,
            "production_db_write": True,
            "public_exposure": True,
        },
    }
