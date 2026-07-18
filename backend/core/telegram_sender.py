"""
Controlled Telegram sender module — Phase 7A.

All sends are gated behind an explicit multi-flag check.  The function never
makes a network call unless every gate passes.  Callers receive a structured
result dict so they can log/return details without touching token values.
"""
import os
import httpx
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# ── helpers ─────────────────────────────────────────────────────────────────

def _env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def _value(name: str) -> str:
    return os.environ.get(name, "").strip()


def _configured(name: str) -> bool:
    return bool(_value(name))


def _telegram_token() -> str:
    """Return the first configured token (primary takes priority over alias)."""
    return _value("TELEGRAM_BOT_TOKEN") or _value("TELEGRAM_TOKEN")


def _chat_id() -> str:
    return _value("TELEGRAM_CHAT_ID")


def _mask_chat(chat_id: str) -> str:
    if len(chat_id) > 4:
        return f"***{chat_id[-4:]}"
    return "***"


# ── gate evaluation ──────────────────────────────────────────────────────────

def evaluate_test_send_gates() -> Dict[str, Any]:
    """
    Evaluate all gates required for a manual test-send.

    Returns a dict with individual gate states and the aggregate
    can_run_test_send boolean.  Never returns token/chat values.
    """
    test_send_flag = _env_bool("ENABLE_TELEGRAM_TEST_SEND", "false")
    send_flag = _env_bool("ENABLE_TELEGRAM_SEND", "false")
    scheduler_flag = _env_bool("ENABLE_ALERT_SCHEDULER", "false")
    token_ok = bool(_telegram_token())
    chat_ok = bool(_chat_id())

    scheduler_blocked = scheduler_flag  # scheduler must be OFF

    all_pass = (
        test_send_flag
        and send_flag
        and not scheduler_blocked
        and token_ok
        and chat_ok
    )

    blocked_reasons = []
    if not test_send_flag:
        blocked_reasons.append("ENABLE_TELEGRAM_TEST_SEND is false")
    if not send_flag:
        blocked_reasons.append("ENABLE_TELEGRAM_SEND is false")
    if scheduler_blocked:
        blocked_reasons.append("ENABLE_ALERT_SCHEDULER must be false")
    if not token_ok:
        blocked_reasons.append("No Telegram token configured")
    if not chat_ok:
        blocked_reasons.append("TELEGRAM_CHAT_ID not configured")

    return {
        "gate_test_send_flag": test_send_flag,
        "gate_send_flag": send_flag,
        "gate_scheduler_off": not scheduler_blocked,
        "gate_token_configured": token_ok,
        "gate_chat_id_configured": chat_ok,
        "can_run_test_send": all_pass,
        "network_call_allowed_for_test_send": all_pass,
        "test_send_requires_manual_enablement": not all_pass,
        "blocked_reasons": blocked_reasons,
        "test_send_gate_status": "open" if all_pass else "locked",
    }


# ── sender ───────────────────────────────────────────────────────────────────

async def send_telegram_test_message(
    custom_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Attempt to send a manual test message to the configured Telegram chat.

    Always re-evaluates gates at call time.  Returns a structured result dict;
    never raises on gate failure.  The actual HTTP call is performed only when
    all gates pass.
    """
    gates = evaluate_test_send_gates()

    if not gates["can_run_test_send"]:
        return {
            "sent": False,
            "dry_run": True,
            "network_call_made": False,
            "gate_status": gates["test_send_gate_status"],
            "blocked_reasons": gates["blocked_reasons"],
            "can_run_test_send": False,
            "message": "Test-send blocked by gate check. No network call was made.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # All gates pass — make the HTTP call.
    token = _telegram_token()
    chat_id = _chat_id()
    masked_chat = _mask_chat(chat_id)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = custom_text or (
        f"GHBS TASI — Manual Test-Send\n"
        f"Phase: 7A\n"
        f"Time (UTC): {ts}\n"
        f"Mode: MANUAL TEST ONLY"
    )

    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = await client.post(
                url,
                json={"chat_id": chat_id, "text": text},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("ok"):
            return {
                "sent": True,
                "dry_run": False,
                "network_call_made": True,
                "gate_status": "open",
                "blocked_reasons": [],
                "can_run_test_send": True,
                "target_chat_masked": masked_chat,
                "message": "Test message sent successfully.",
                "timestamp": ts,
            }
        return {
            "sent": False,
            "dry_run": False,
            "network_call_made": True,
            "gate_status": "open",
            "blocked_reasons": [f"Telegram API error: {data.get('description', 'unknown')}"],
            "can_run_test_send": True,
            "target_chat_masked": masked_chat,
            "message": "Telegram API returned an error.",
            "timestamp": ts,
        }

    except Exception:
        return {
            "sent": False,
            "dry_run": False,
            "network_call_made": True,
            "gate_status": "open",
            "blocked_reasons": ["Network or HTTP error — check token, chat ID, and connectivity."],
            "can_run_test_send": True,
            "target_chat_masked": masked_chat,
            "message": "Delivery failed. Check bot token, chat ID, or connectivity.",
            "timestamp": ts,
        }
