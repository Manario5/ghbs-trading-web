"""
Scheduler & automated alerts readiness — Release Train E.

Defines the future scheduled alert jobs and evaluates the gates required to
run them. NOTHING here starts a scheduler or sends anything — this is
readiness/visibility only. Job definitions are data, not running tasks.

Scheduled real sends require ALL of:
- ENABLE_ALERT_SCHEDULER=true
- ENABLE_TELEGRAM_SEND=true
- Telegram token (TELEGRAM_BOT_TOKEN or TELEGRAM_TOKEN) configured
- TELEGRAM_CHAT_ID configured
- Safety gate pass: production DB disabled (ALLOW_PRODUCTION_DB=false)

Note the deliberate asymmetry with the Phase 7A manual test-send (which
requires the scheduler to be OFF): the two paths can never be enabled by the
same configuration, so a single .env state cannot both auto-send and
manual-test-send.
"""
import os
from typing import Any, Dict, List

from backend.core.alert_audit import record_alert_attempt

# Declarative job registry — templates come from backend/core/alert_templates.py.
SCHEDULED_JOB_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "job_id": "daily_system_health",
        "template_id": "system_health",
        "description": "Daily system health summary",
        "default_interval_seconds": 86400,
        "category": "system",
    },
    {
        "job_id": "scout_summary",
        "template_id": "scout_summary_test",
        "description": "Post-scan scout summary (requires live scout to be enabled separately)",
        "default_interval_seconds": 86400,
        "category": "system",
    },
    {
        "job_id": "dry_run_heartbeat",
        "template_id": "general_test",
        "description": "Dry-run heartbeat used by the existing dry-run scheduler",
        "default_interval_seconds": 300,
        "category": "test",
    },
]


def _env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def _configured(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def evaluate_scheduled_send_gates() -> Dict[str, Any]:
    """Gates for REAL scheduled sends (future capability — currently always locked in practice)."""
    scheduler_flag = _env_bool("ENABLE_ALERT_SCHEDULER")
    send_flag = _env_bool("ENABLE_TELEGRAM_SEND")
    token_ok = _configured("TELEGRAM_BOT_TOKEN") or _configured("TELEGRAM_TOKEN")
    chat_ok = _configured("TELEGRAM_CHAT_ID")
    prod_db_off = not _env_bool("ALLOW_PRODUCTION_DB")

    blocked_reasons: List[str] = []
    if not scheduler_flag:
        blocked_reasons.append("ENABLE_ALERT_SCHEDULER is false")
    if not send_flag:
        blocked_reasons.append("ENABLE_TELEGRAM_SEND is false")
    if not token_ok:
        blocked_reasons.append("No Telegram token configured")
    if not chat_ok:
        blocked_reasons.append("TELEGRAM_CHAT_ID not configured")
    if not prod_db_off:
        blocked_reasons.append("ALLOW_PRODUCTION_DB must be false")

    can_send = not blocked_reasons
    return {
        "gate_scheduler_flag": scheduler_flag,
        "gate_send_flag": send_flag,
        "gate_token_configured": token_ok,
        "gate_chat_id_configured": chat_ok,
        "gate_production_db_off": prod_db_off,
        "can_run_scheduled_sends": can_send,
        "scheduled_send_gate_status": "open" if can_send else "locked",
        "blocked_reasons": blocked_reasons,
    }


def get_scheduler_readiness() -> Dict[str, Any]:
    gates = evaluate_scheduled_send_gates()
    scheduler_flag = gates["gate_scheduler_flag"]
    dry_run_only = _env_bool("ALERT_SCHEDULER_DRY_RUN_ONLY", "true")

    return {
        "scheduler_enabled_in_env": scheduler_flag,
        "dry_run_only": dry_run_only,
        "job_definitions": SCHEDULED_JOB_DEFINITIONS,
        "jobs_defined": len(SCHEDULED_JOB_DEFINITIONS),
        "jobs_running": 0 if not scheduler_flag else None,  # None = ask /scheduler/status for live state
        "gates": gates,
        "auto_start_on_boot": False,
        "real_scheduled_sends_implemented": False,
        "safety_state": "SAFE" if not scheduler_flag else "WARNING",
        "locked_reason": (
            "Scheduler locked by default configuration"
            if not scheduler_flag
            else "ENABLE_ALERT_SCHEDULER is true — verify this is intentional"
        ),
    }


def record_scheduled_attempt(job_id: str, outcome: str, blocked_reasons: List[str]) -> None:
    """Audit a scheduled alert attempt via the Train A audit layer."""
    record_alert_attempt({
        "kind": "scheduled",
        "outcome": outcome,
        "gate_status": "locked" if blocked_reasons else "open",
        "network_call_made": outcome == "sent",
        "blocked_reasons": blocked_reasons,
        "template_id": job_id,
    })
