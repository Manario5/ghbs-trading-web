import os
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from backend.auth.dependencies import get_current_user
import httpx
from anthropic import AsyncAnthropic

router = APIRouter()

class TestResponse(BaseModel):
    success: bool
    message: str
    metadata: Dict[str, Any] = {}

def assert_smoke_tests_enabled():
    enabled = os.environ.get("ENABLE_API_SMOKE_TESTS", "false").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=400, detail="API smoke tests are completely disabled in this environment.")

def _first_configured(*names: str) -> str:
    """Return the first env var name that holds a non-empty value, else ''."""
    for name in names:
        if os.environ.get(name, "").strip():
            return name
    return ""

@router.get("/status")
def get_integrations_status(current_user: dict = Depends(get_current_user)):
    anthropic_configured = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())

    # Alias-aware Telegram detection (UAT requirement #8): primary
    # TELEGRAM_BOT_TOKEN, alias TELEGRAM_TOKEN, and legacy WEBAPP_TELEGRAM_BOT_TOKEN.
    token_source = _first_configured(
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN", "WEBAPP_TELEGRAM_BOT_TOKEN"
    )
    chat_source = _first_configured("TELEGRAM_CHAT_ID", "WEBAPP_TELEGRAM_CHAT_ID")
    telegram_bot_configured = bool(token_source)
    telegram_chat_configured = bool(chat_source)
    telegram_ready = telegram_bot_configured and telegram_chat_configured

    return {
        "anthropic": {
            "configured": anthropic_configured,
            "status_text": "Configured" if anthropic_configured else "Not Configured"
        },
        "telegram_alert_bot": {
            "configured": telegram_ready,
            "status_text": "Configured" if telegram_ready else "Not Configured",
            "token_configured": telegram_bot_configured,
            "chat_id_configured": telegram_chat_configured,
            "token_source": token_source or "missing"
        }
    }

@router.post("/anthropic/test", response_model=TestResponse)
async def test_anthropic(current_user: dict = Depends(get_current_user)):
    assert_smoke_tests_enabled()
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY is missing.")
        
    try:
        model_name = os.environ.get("ANTHROPIC_SMOKE_TEST_MODEL", "claude-haiku-4-5-20251001")
        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=model_name,
            max_tokens=20,
            messages=[{"role": "user", "content": "Reply with OK only."}]
        )
        return TestResponse(
            success=True,
            message="Anthropic smoke test passed.",
            metadata={
                "model_used": model_name,
                "response_text": response.content[0].text
            }
        )
    except Exception as e:
        return TestResponse(
            success=False,
            message=f"Anthropic test failed: {str(e)}"
        )

@router.post("/telegram/test", response_model=TestResponse)
async def test_telegram(current_user: dict = Depends(get_current_user)):
    assert_smoke_tests_enabled()
    
    bot_token = os.environ.get("WEBAPP_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("WEBAPP_TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="Telegram Bot Token or Chat ID is missing.")
        
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": "GHBS TASI Command Center Telegram test."
            }
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("ok"):
                return TestResponse(
                    success=True,
                    message="Telegram smoke test passed.",
                    metadata={"target_chat": f"***{str(chat_id)[-4:]}" if len(str(chat_id)) > 4 else "***"}
                )
            else:
                return TestResponse(
                    success=False,
                    message=f"Telegram API reported error.",
                    metadata={"error": data.get("description")}
                )
    except Exception as e:
        return TestResponse(
            success=False,
            message="Telegram delivery failed. Check bot token, chat ID, or bot access."
        )
