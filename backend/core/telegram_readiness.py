import os
import datetime
from typing import Any, Dict, Optional


def _env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def _value(name: str) -> str:
    return os.environ.get(name, "").strip()


def _configured(name: str) -> bool:
    return bool(_value(name))


def _masked_status(name: str) -> str:
    return "configured" if _configured(name) else "missing"


def _telegram_token_value() -> str:
    primary = _value("TELEGRAM_BOT_TOKEN")
    alias = _value("TELEGRAM_TOKEN")
    return primary or alias


def _telegram_token_source() -> str:
    if _configured("TELEGRAM_BOT_TOKEN"):
        return "TELEGRAM_BOT_TOKEN"
    if _configured("TELEGRAM_TOKEN"):
        return "TELEGRAM_TOKEN"
    return "missing"


def _authorized_user_ids_count() -> int:
    raw = _value("AUTHORIZED_USER_IDS")
    if not raw:
        return 0
    return len([part.strip() for part in raw.split(",") if part.strip()])


def get_telegram_alert_status() -> Dict[str, Any]:
    from backend.core.telegram_sender import evaluate_test_send_gates

    token_value = _telegram_token_value()
    token_configured = bool(token_value)
    chat_configured = _configured("TELEGRAM_CHAT_ID")
    authorized_ids_configured = _configured("AUTHORIZED_USER_IDS")

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
        else "One or more Telegram send/test/scheduler flags are enabled"
    )

    gates = evaluate_test_send_gates()

    return {
        "telegram_bot_token_configured": token_configured,
        "telegram_chat_id_configured": chat_configured,
        "telegram_bot_token_masked": "configured" if token_configured else "missing",
        "telegram_chat_id_masked": _masked_status("TELEGRAM_CHAT_ID"),
        "telegram_token_source": _telegram_token_source(),
        "telegram_token_alias_configured": _configured("TELEGRAM_TOKEN"),
        "telegram_token_alias_used": (not _configured("TELEGRAM_BOT_TOKEN")) and _configured("TELEGRAM_TOKEN"),
        "authorized_user_ids_configured": authorized_ids_configured,
        "authorized_user_ids_masked": "configured" if authorized_ids_configured else "missing",
        "authorized_user_ids_count": _authorized_user_ids_count(),
        "telegram_dry_run_enabled": dry_run_enabled,
        "telegram_send_enabled": send_enabled,
        "telegram_test_send_enabled": test_send_enabled,
        "alert_scheduler_enabled": alert_scheduler_enabled,
        "can_send_telegram": False,
        "can_run_test_send": gates["can_run_test_send"],
        "test_send_gate_status": gates["test_send_gate_status"],
        "test_send_requires_manual_enablement": gates["test_send_requires_manual_enablement"],
        "network_call_allowed_for_test_send": gates["network_call_allowed_for_test_send"],
        "telegram_network_calls_locked": not gates["can_run_test_send"],
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
