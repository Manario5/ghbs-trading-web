import os
import datetime
from typing import Any, Dict, Optional


def _env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def _configured(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def _masked_status(name: str) -> str:
    return "configured" if _configured(name) else "missing"


def get_telegram_alert_status() -> Dict[str, Any]:
    token_configured = _configured("TELEGRAM_BOT_TOKEN")
    chat_configured = _configured("TELEGRAM_CHAT_ID")

    dry_run_enabled = _env_bool("ENABLE_TELEGRAM_DRY_RUN", "true")
    send_enabled = _env_bool("ENABLE_TELEGRAM_SEND", "false")
    test_send_enabled = _env_bool("ENABLE_TELEGRAM_TEST_SEND", "false")
    alert_scheduler_enabled = _env_bool("ENABLE_ALERT_SCHEDULER", "false")

    risky_flags = [
        send_enabled,
        test_send_enabled,
        alert_scheduler_enabled,
    ]

    safety_state = "SAFE" if not any(risky_flags) else "WARNING"

    locked_reason = (
        "Telegram sending locked by default configuration"
        if safety_state == "SAFE"
        else "Telegram send/test/scheduler flags are not allowed in Phase 6W"
    )

    return {
        "telegram_bot_token_configured": token_configured,
        "telegram_chat_id_configured": chat_configured,
        "telegram_bot_token_masked": _masked_status("TELEGRAM_BOT_TOKEN"),
        "telegram_chat_id_masked": _masked_status("TELEGRAM_CHAT_ID"),
        "telegram_dry_run_enabled": dry_run_enabled,
        "telegram_send_enabled": send_enabled,
        "telegram_test_send_enabled": test_send_enabled,
        "alert_scheduler_enabled": alert_scheduler_enabled,
        "can_send_telegram": False,
        "can_run_test_send": False,
        "telegram_network_calls_locked": True,
        "safety_state": safety_state,
        "locked_reason": locked_reason,
    }


def build_telegram_dry_run_preview(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = payload or {}
    status = get_telegram_alert_status()

    template_type = str(payload.get("template_type", "generic_alert"))
    ticker = str(payload.get("ticker", "SAMPLE"))
    signal = str(payload.get("signal", "WATCH"))
    setup_type = str(payload.get("setup_type", "DRY_RUN"))
    note = str(payload.get("note", "Dry-run preview only. No Telegram message was sent."))

    message_preview = (
        "GHBS TASI Alert Preview\n"
        f"Ticker: {ticker}\n"
        f"Signal: {signal}\n"
        f"Setup: {setup_type}\n"
        "Mode: DRY RUN ONLY\n"
        f"Note: {note}"
    )

    return {
        "dry_run": True,
        "would_send": False,
        "channel": "telegram",
        "template_type": template_type,
        "message_preview": message_preview,
        "execution_allowed": False,
        "telegram_send_enabled": status["telegram_send_enabled"],
        "telegram_test_send_enabled": status["telegram_test_send_enabled"],
        "telegram_network_calls_locked": status["telegram_network_calls_locked"],
        "safety_state": status["safety_state"],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
