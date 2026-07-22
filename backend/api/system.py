from datetime import datetime, timezone
import os
from fastapi import APIRouter
from backend.models.schemas import SystemHealth, SystemVersion

router = APIRouter()

@router.get("/health", response_model=SystemHealth)
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/version", response_model=SystemVersion)
async def system_version():
    return {
        "ghbs_version": "1.0.0-alpha",
        "tasi_version": "V7.2.1"
    }

@router.get("/config")
async def system_config():
    from backend.core.config import CFG
    from backend.db.database import get_db_path
    import dataclasses
    d = dataclasses.asdict(CFG)
    d["db_path"] = get_db_path()
    return d

@router.get("/safety-matrix")
async def safety_matrix():
    from backend.db.database import get_db_path
    from backend.core.execution_guard import get_execution_guard_status
    from backend.core.telegram_readiness import get_telegram_alert_status

    allow_prod = os.environ.get("ALLOW_PRODUCTION_DB", "false").lower() == "true"
    db_path = get_db_path()
    live_analyze = os.environ.get("ENABLE_LIVE_ANALYZE_PREVIEW", "false").lower() == "true"
    live_scout = os.environ.get("ENABLE_LIVE_SCOUT_PREVIEW", "false").lower() == "true"
    alert_sched = os.environ.get("ENABLE_ALERT_SCHEDULER", "false").lower() == "true"
    cov_scan = os.environ.get("ENABLE_PROVIDER_COVERAGE_SCAN", "false").lower() == "true"
    api_smoke = os.environ.get("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"

    gate_enabled = os.environ.get("ENABLE_PRODUCTION_DB_READONLY_GATE", "false").lower() == "true"
    ro_required = os.environ.get("PRODUCTION_DB_READONLY_REQUIRED", "true").lower() == "true"
    prod_path_configured = bool(os.environ.get("PRODUCTION_DB_PATH", "").strip())

    tg_token_configured = (
        len(os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()) > 0
        or len(os.environ.get("TELEGRAM_TOKEN", "").strip()) > 0
    )
    anth_configured = len(os.environ.get("ANTHROPIC_API_KEY", "").strip()) > 0

    tg_masked = "configured" if tg_token_configured else "not configured"
    anth_masked = "configured" if anth_configured else "not configured"

    exec_status = get_execution_guard_status()
    tg_status = get_telegram_alert_status()

    from backend.core.safety_state import compute_safety_state
    derived = compute_safety_state(db_path, any(exec_status.values()))
    state = derived["safety_state"]

    return {
        "mode_label": derived["mode_label"],
        "warning_reasons": derived["warning_reasons"],
        "unsafe_reasons": derived["unsafe_reasons"],
        "safety_reasons": derived["reasons"],
        "allow_production_db": allow_prod,
        "db_path": db_path,
        "production_db_readonly_gate_enabled": gate_enabled,
        "production_db_path_configured": prod_path_configured,
        "production_db_readonly_required": ro_required,
        "live_analyze_preview_enabled": live_analyze,
        "live_scout_preview_enabled": live_scout,
        "alert_scheduler_enabled": alert_sched,
        "provider_coverage_scan_enabled": cov_scan,
        "api_smoke_tests_enabled": api_smoke,
        "market_data_smoke_tests_enabled": api_smoke,
        "provider_readiness_safe": not (api_smoke or cov_scan or live_analyze or live_scout),
        "provider_calls_locked": not (api_smoke or cov_scan or live_analyze or live_scout),
        "telegram_dry_run_enabled": tg_status.get("telegram_dry_run_enabled", True),
        "telegram_send_enabled": tg_status.get("telegram_send_enabled", False),
        "telegram_test_send_enabled": tg_status.get("telegram_test_send_enabled", False),
        "telegram_network_calls_locked": tg_status.get("telegram_network_calls_locked", True),
        "telegram_readiness_safe": tg_status.get("safety_state") == "SAFE",
        "telegram_token_source": tg_status.get("telegram_token_source", "missing"),
        "telegram_token_alias_configured": tg_status.get("telegram_token_alias_configured", False),
        "telegram_token_alias_used": tg_status.get("telegram_token_alias_used", False),
        "authorized_user_ids_configured": tg_status.get("authorized_user_ids_configured", False),
        "authorized_user_ids_masked": tg_status.get("authorized_user_ids_masked", "missing"),
        "authorized_user_ids_count": tg_status.get("authorized_user_ids_count", 0),
        "telegram_configured_masked": tg_masked,
        "can_run_test_send": tg_status.get("can_run_test_send", False),
        "test_send_gate_status": tg_status.get("test_send_gate_status", "locked"),
        "test_send_requires_manual_enablement": tg_status.get("test_send_requires_manual_enablement", True),
        "network_call_allowed_for_test_send": tg_status.get("network_call_allowed_for_test_send", False),
        "anthropic_configured_masked": anth_masked,
        "active_environment": os.environ.get("ENVIRONMENT", "development"),
        "safety_state": state
    }

@router.get("/secret-status")
async def secret_status():
    from backend.core.secrets import get_secret_status
    return get_secret_status()

@router.get("/health-deep")
async def health_deep():
    """Deep health check (Release Train F): DB connectivity + safety state. No secrets."""
    from backend.db.database import get_db_path
    db_ok = False
    db_error = None
    try:
        import aiosqlite
        async with aiosqlite.connect(get_db_path()) as db:
            async with db.execute("SELECT 1") as cur:
                row = await cur.fetchone()
                db_ok = row is not None and row[0] == 1
    except Exception as exc:  # report class only — no paths/values
        db_error = type(exc).__name__

    matrix = await safety_matrix()
    return {
        "status": "ok" if db_ok else "degraded",
        "db_connectivity": db_ok,
        "db_error_class": db_error,
        "safety_state": matrix["safety_state"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/ops-status")
async def ops_status():
    """
    Consolidated operational status (Release Train F).
    Aggregates every readiness surface into one masked, secret-free response.
    """
    from backend.core.secrets import get_secret_status
    from backend.core.provider_health import get_provider_health
    from backend.core.preview_readiness import get_preview_readiness
    from backend.core.scheduler_readiness import get_scheduler_readiness
    from backend.core.telegram_readiness import get_telegram_alert_status

    matrix = await safety_matrix()
    return {
        "safety_matrix": matrix,
        "secrets_masked": get_secret_status(),
        "provider_health": get_provider_health(),
        "preview_readiness": get_preview_readiness(),
        "scheduler_readiness": get_scheduler_readiness(),
        "telegram_readiness": get_telegram_alert_status(),
        "overall_state": matrix["safety_state"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/db-gate-status")
async def db_gate_status():
    from backend.core.db_gate import get_db_gate_status
    return get_db_gate_status()

@router.get("/provider-readiness-status")
async def provider_readiness_status():
    from backend.core.provider_readiness import get_provider_readiness_status
    return get_provider_readiness_status()

@router.get("/live-preview-status")
async def live_preview_status():
    from backend.core.execution_guard import get_execution_guard_status
    
    live_analyze = os.environ.get("ENABLE_LIVE_ANALYZE_PREVIEW", "false").lower() == "true"
    live_scout = os.environ.get("ENABLE_LIVE_SCOUT_PREVIEW", "false").lower() == "true"
    alert_sched = os.environ.get("ENABLE_ALERT_SCHEDULER", "false").lower() == "true"
    cov_scan = os.environ.get("ENABLE_PROVIDER_COVERAGE_SCAN", "false").lower() == "true"
    
    exec_status = get_execution_guard_status()
    exec_active = any(exec_status.values())

    from backend.db.database import get_db_path
    from backend.core.safety_state import compute_safety_state
    derived = compute_safety_state(get_db_path(), exec_active)

    # Manual preview is blocked (independently of the display state) whenever an
    # overlapping capability is active. Kept separate from safety_state so the
    # label stays consistent with the safety matrix (UAT requirement #5).
    blocked_reason = None
    if exec_active:
        blocked_reason = "Execution guard reported active execution capabilities"
    elif alert_sched:
        blocked_reason = "Scheduler must be disabled for manual preview"
    elif cov_scan:
        blocked_reason = "Provider coverage scan must be disabled for manual preview"

    if blocked_reason is not None:
        reason = blocked_reason
    elif not live_analyze and not live_scout:
        reason = "Locked by default configuration"
    else:
        reason = "Live preview enabled (read-only, no execution, no production DB write)"

    return {
        "live_analyze_preview_enabled": live_analyze,
        "live_scout_preview_enabled": live_scout,
        "scheduler_enabled": alert_sched,
        "provider_coverage_scan_enabled": cov_scan,
        **exec_status,
        "production_db_write_enabled": False, # Guarded by gate
        "safety_state": derived["safety_state"],
        "mode_label": derived["mode_label"],
        "warning_reasons": derived["warning_reasons"],
        "unsafe_reasons": derived["unsafe_reasons"],
        "can_manual_analyze_preview": live_analyze and blocked_reason is None,
        "can_manual_scout_preview": live_scout and blocked_reason is None,
        "locked_reason": reason
    }


@router.get("/telegram-alert-status")
async def telegram_alert_status():
    from backend.core.telegram_readiness import get_telegram_alert_status
    return get_telegram_alert_status()
