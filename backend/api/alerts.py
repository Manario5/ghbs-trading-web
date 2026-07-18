import os
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from backend.auth.dependencies import get_current_user
from backend.db.database import get_db

router = APIRouter()

class TestResponse(BaseModel):
    success: bool
    message: str
    metadata: Dict[str, Any] = {}

class TemplateRequest(BaseModel):
    template_id: str
    preview_message: str

def assert_smoke_tests_enabled():
    enabled = os.environ.get("ENABLE_API_SMOKE_TESTS", "false").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=400, detail="API smoke tests are completely disabled in this environment.")

async def log_alert_event(db, alert_type: str, title: str, message: str, delivery_status: str, 
                          destination_masked: str, user_id: int, current_time: str):
    await db.execute("""
        INSERT INTO alert_events (
            alert_type, title, message, delivery_status, destination_masked, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (alert_type, title, message, delivery_status, destination_masked, user_id, current_time))
    await db.commit()

@router.post("/manual-test", response_model=TestResponse)
async def manual_telegram_test(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    assert_smoke_tests_enabled()
    
    bot_token = os.environ.get("WEBAPP_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("WEBAPP_TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="Telegram Bot Token or Chat ID is missing.")
        
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    masked_chat = f"***{str(chat_id)[-4:]}" if len(str(chat_id)) > 4 else "***"
    text_content = f"GHBS TASI Web App Manual Alert Test\\nSandbox Time: {current_time}"
            
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text_content
            }
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            user_id = current_user.get("id", None)
            
            if data.get("ok"):
                # Record in audit log
                await db.execute("""
                    INSERT INTO audit_events (
                        user_id, action_type, object_type, object_id, timestamp, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id, "test_alert", "manual_alert", "telegram", current_time, 
                    "Sent manual Telegram alert test."
                ))
                
                # Record in alert log
                await log_alert_event(db, "manual_test", "Manual Alert", text_content, "SENT", masked_chat, user_id, current_time)

                return TestResponse(
                    success=True,
                    message="Manual Telegram alert sent.",
                    metadata={"target_chat": masked_chat}
                )
            else:
                await log_alert_event(db, "manual_test", "Manual Alert", text_content, "FAILED", masked_chat, user_id, current_time)
                return TestResponse(
                    success=False,
                    message=f"Telegram API reported error.",
                    metadata={"error": data.get("description")}
                )
    except httpx.HTTPStatusError as e:
        user_id = current_user.get("id", None)
        sanitized_msg = "Telegram delivery failed. Check bot token, chat ID, or bot access."
        await log_alert_event(db, "manual_test", "Manual Alert", text_content, "FAILED", masked_chat, user_id, current_time)
        return TestResponse(
            success=False,
            message=sanitized_msg
        )
    except Exception as e:
        user_id = current_user.get("id", None)
        sanitized_msg = "Telegram delivery failed. Check bot token, chat ID, or bot access."
        await log_alert_event(db, "manual_test", "Manual Alert", text_content, "FAILED", masked_chat, user_id, current_time)
        return TestResponse(
            success=False,
            message=sanitized_msg
        )

@router.post("/send-template", response_model=TestResponse)
async def send_template(req: TemplateRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    assert_smoke_tests_enabled()
    
    bot_token = os.environ.get("WEBAPP_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("WEBAPP_TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        raise HTTPException(status_code=400, detail="Telegram Bot Token or Chat ID is missing.")
        
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    masked_chat = f"***{str(chat_id)[-4:]}" if len(str(chat_id)) > 4 else "***"
    user_id = current_user.get("id", None)
    
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": req.preview_message
            }
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            if data.get("ok"):
                await log_alert_event(db, req.template_id, f"Template: {req.template_id}", req.preview_message, "SENT", masked_chat, user_id, current_time)
                return TestResponse(
                    success=True,
                    message="Manual template alert sent.",
                    metadata={"target_chat": masked_chat}
                )
            else:
                desc = data.get("description", "Unknown error")
                await log_alert_event(db, req.template_id, f"Template: {req.template_id}", req.preview_message, f"FAILED: {desc}", masked_chat, user_id, current_time)
                return TestResponse(
                    success=False,
                    message=f"Telegram API reported error.",
                    metadata={"error": desc}
                )
    except httpx.HTTPStatusError as e:
        sanitized_msg = "Telegram delivery failed. Check bot token, chat ID, or bot access."
        await log_alert_event(db, req.template_id, f"Template: {req.template_id}", req.preview_message, "FAILED", masked_chat, user_id, current_time)
        return TestResponse(
            success=False,
            message=sanitized_msg
        )
    except Exception as e:
        sanitized_msg = "Telegram delivery failed. Check bot token, chat ID, or bot access."
        await log_alert_event(db, req.template_id, f"Template: {req.template_id}", req.preview_message, "FAILED", masked_chat, user_id, current_time)
        return TestResponse(
            success=False,
            message=sanitized_msg
        )

@router.get("/log")
async def get_alerts_log(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    async with db.execute("""
        SELECT a.*, u.username 
        FROM alert_events a
        LEFT JOIN users u ON a.created_by = u.id
        ORDER BY a.id DESC LIMIT 100
    """) as cur:
        rows = await cur.fetchall()
        return [dict(row) for row in rows]


from typing import Dict, Any
from fastapi import Depends as _Depends
from backend.auth.dependencies import get_current_user as _get_current_user
from backend.core.telegram_readiness import build_telegram_dry_run_preview


@router.post("/telegram/dry-run-preview")
async def telegram_dry_run_preview(
    payload: Dict[str, Any] | None = None,
    current_user: dict = _Depends(_get_current_user),
):
    return build_telegram_dry_run_preview(payload or {})


@router.post("/telegram/test-send")
async def telegram_test_send(current_user: dict = _Depends(_get_current_user)):
    """
    Controlled manual test-send endpoint.

    Makes a real Telegram network call only when all five gates pass:
      - ENABLE_TELEGRAM_TEST_SEND=true
      - ENABLE_TELEGRAM_SEND=true
      - ENABLE_ALERT_SCHEDULER=false
      - TELEGRAM_BOT_TOKEN or TELEGRAM_TOKEN configured
      - TELEGRAM_CHAT_ID configured

    Otherwise returns a locked status with no network call.
    Secret values are never included in the response.
    """
    from backend.core.telegram_sender import send_telegram_test_message, evaluate_test_send_gates

    gates = evaluate_test_send_gates()

    if not gates["can_run_test_send"]:
        return {
            "sent": False,
            "dry_run": True,
            "network_call_made": False,
            "gate_status": gates["test_send_gate_status"],
            "can_run_test_send": False,
            "test_send_requires_manual_enablement": True,
            "network_call_allowed_for_test_send": False,
            "blocked_reasons": gates["blocked_reasons"],
            "message": "Test-send is locked. All gates must be manually enabled. No network call was made.",
        }

    result = await send_telegram_test_message()

    # Strip any token/chat values that might have been set upstream; return only safe fields.
    return {
        "sent": result["sent"],
        "dry_run": result["dry_run"],
        "network_call_made": result["network_call_made"],
        "gate_status": result["gate_status"],
        "can_run_test_send": True,
        "test_send_requires_manual_enablement": False,
        "network_call_allowed_for_test_send": True,
        "blocked_reasons": result["blocked_reasons"],
        "target_chat_masked": result.get("target_chat_masked", "***"),
        "message": result["message"],
        "timestamp": result.get("timestamp", ""),
    }
