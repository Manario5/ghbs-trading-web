import os
from typing import Dict, Any

def _is_configured(key_name: str) -> bool:
    val = os.environ.get(key_name, "")
    return bool(val.strip())

def get_secret_status() -> Dict[str, Any]:
    anthropic = _is_configured("ANTHROPIC_API_KEY")
    tg_token = _is_configured("TELEGRAM_BOT_TOKEN")
    tg_chat = _is_configured("TELEGRAM_CHAT_ID")
    twelve = _is_configured("TWELVEDATA_API_KEY")
    sahmk = _is_configured("SAHMK_API_KEY")
    tradingview = _is_configured("TRADINGVIEW_API_KEY")
    
    return {
        "anthropic": {
            "configured": anthropic,
        },
        "telegram": {
            "bot_token_configured": tg_token,
            "chat_id_configured": tg_chat,
            "ready_for_notifications": tg_token and tg_chat,
        },
        "market_data": {
            "twelvedata_configured": twelve,
            "sahmk_configured": sahmk,
            "tradingview_configured": tradingview,
        },
        "summary": {
            "any_secrets_configured": any([anthropic, tg_token, tg_chat, twelve, sahmk, tradingview])
        }
    }
