"""
Canonical safety-state derivation — UAT live UI fixes.

Single source of truth for the SAFE / WARNING(LIVE-UAT) / UNSAFE model so that
every panel (safety matrix, live-preview status, ops status) reports the same
state and the same human-readable reasons.

Model (see UAT requirement #5):
- SAFE     : all gates locked.
- WARNING  : live preview / provider / market-data / Telegram send-or-test
             gates enabled, but NO execution and NO production DB write.
             Presented to operators as "LIVE-UAT".
- UNSAFE   : truly dangerous — production DB write path, active execution
             capability. (Public exposure is enforced at the network layer,
             not derivable from env here.)

No secrets are read or returned by this module.
"""
import os
from typing import Any, Dict, List


def _bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def compute_safety_state(db_path: str, exec_active: bool) -> Dict[str, Any]:
    allow_prod = _bool("ALLOW_PRODUCTION_DB")
    ro_required = os.environ.get("PRODUCTION_DB_READONLY_REQUIRED", "true").strip().lower() == "true"

    live_analyze = _bool("ENABLE_LIVE_ANALYZE_PREVIEW")
    live_scout = _bool("ENABLE_LIVE_SCOUT_PREVIEW")
    alert_sched = _bool("ENABLE_ALERT_SCHEDULER")
    cov_scan = _bool("ENABLE_PROVIDER_COVERAGE_SCAN")
    api_smoke = _bool("ENABLE_MARKET_DATA_SMOKE_TESTS")
    telegram_send = _bool("ENABLE_TELEGRAM_SEND")
    telegram_test = _bool("ENABLE_TELEGRAM_TEST_SEND")

    is_test_db = "tasi_ledger_test.db" in db_path

    unsafe_reasons: List[str] = []
    if allow_prod and not is_test_db:
        unsafe_reasons.append("Production DB access enabled with a non-test database")
    if allow_prod and not ro_required:
        unsafe_reasons.append("Production DB access enabled without read-only requirement")
    if ("tasi_ledger.db" in db_path) and not is_test_db:
        unsafe_reasons.append("Production ledger database path is active")
    if exec_active:
        unsafe_reasons.append("Execution guard reported active execution capability")

    # WARNING gates — listed ONLY when actually enabled. Scheduler appears here
    # solely when ENABLE_ALERT_SCHEDULER is true (UAT requirement #4).
    warning_reasons: List[str] = []
    if cov_scan:
        warning_reasons.append("Provider coverage scan enabled")
    if api_smoke:
        warning_reasons.append("Market data smoke tests enabled")
    if live_analyze:
        warning_reasons.append("Live Analyze Preview enabled")
    if live_scout:
        warning_reasons.append("Live Scout Preview enabled")
    if alert_sched:
        warning_reasons.append("Alert Scheduler enabled")
    if telegram_send:
        warning_reasons.append("Telegram send enabled")
    if telegram_test:
        warning_reasons.append("Telegram test-send enabled")

    if unsafe_reasons:
        state, mode = "UNSAFE", "UNSAFE"
    elif warning_reasons:
        state, mode = "WARNING", "LIVE-UAT"
    else:
        state, mode = "SAFE", "SAFE"

    return {
        "safety_state": state,
        "mode_label": mode,
        "warning_reasons": warning_reasons,
        "unsafe_reasons": unsafe_reasons,
        "reasons": unsafe_reasons + warning_reasons,
    }
