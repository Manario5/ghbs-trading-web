import os
from typing import Dict, Any


def _value(key_name: str) -> str:
    return os.environ.get(key_name, "").strip()


def _is_configured(key_name: str) -> bool:
    return bool(_value(key_name))


def _masked_status(key_name: str) -> str:
    return "configured" if _is_configured(key_name) else "missing"


def _telegram_token_configured() -> bool:
    return _is_configured("TELEGRAM_BOT_TOKEN") or _is_configured("TELEGRAM_TOKEN")


def _telegram_token_source() -> str:
    if _is_configured("TELEGRAM_BOT_TOKEN"):
        return "TELEGRAM_BOT_TOKEN"
    if _is_configured("TELEGRAM_TOKEN"):
        return "TELEGRAM_TOKEN"
    return "missing"


def _authorized_user_ids_count() -> int:
    raw = _value("AUTHORIZED_USER_IDS")
    if not raw:
        return 0
    return len([part.strip() for part in raw.split(",") if part.strip()])


def get_secret_status() -> Dict[str, Any]:
    anthropic = _is_configured("ANTHROPIC_API_KEY")

    tg_token = _telegram_token_configured()
    tg_alias = _is_configured("TELEGRAM_TOKEN")
    tg_chat = _is_configured("TELEGRAM_CHAT_ID")
    auth_ids = _is_configured("AUTHORIZED_USER_IDS")

    twelve = _is_configured("TWELVEDATA_API_KEY")
    sahmk = _is_configured("SAHMK_API_KEY")
    tradingview = _is_configured("TRADINGVIEW_API_KEY")

    return {
        "anthropic": {
            "configured": anthropic,
            "masked": _masked_status("ANTHROPIC_API_KEY"),
        },
        "telegram": {
            "bot_token_configured": tg_token,
            "bot_token_masked": "configured" if tg_token else "missing",
            "token_source": _telegram_token_source(),
            "token_alias_configured": tg_alias,
            "token_alias_used": (not _is_configured("TELEGRAM_BOT_TOKEN")) and tg_alias,
            "chat_id_configured": tg_chat,
            "chat_id_masked": _masked_status("TELEGRAM_CHAT_ID"),
            "authorized_user_ids_configured": auth_ids,
            "authorized_user_ids_masked": "configured" if auth_ids else "missing",
            "authorized_user_ids_count": _authorized_user_ids_count(),
            "ready_for_notifications": tg_token and tg_chat,
        },
        "market_data": {
            "twelvedata_configured": twelve,
            "sahmk_configured": sahmk,
            "tradingview_configured": tradingview,
        },
        "summary": {
            "any_secrets_configured": any([
                anthropic,
                tg_token,
                tg_chat,
                auth_ids,
                twelve,
                sahmk,
                tradingview,
            ])
        }
    }
