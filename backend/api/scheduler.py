import os
import httpx
import logging
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from backend.auth.dependencies import get_current_user
from backend.db.database import get_db, get_db_path, assert_db_allowed
from backend.api.alerts import log_alert_event

router = APIRouter()
logger = logging.getLogger(__name__)

class SchedulerActionResponse(BaseModel):
    success: bool
    message: str
    status: str

class SchedulerStatusResponse(BaseModel):
    enabled_in_env: bool
    dry_run_only_env: bool
    is_running: bool
    interval_seconds: int
    last_run_at: str | None = None
    next_run_estimate: str | None = None
    total_dry_run_sent: int = 0
    safety_state: str

# Global state for background task
SCHEDULER_TASK: asyncio.Task | None = None
SCHEDULER_STOP_EVENT: asyncio.Event = asyncio.Event()

# Additional state 
LAST_RUN_AT: str | None = None
NEXT_RUN_ESTIMATE: str | None = None
TOTAL_DRY_RUN_SENT: int = 0

def assert_scheduler_enabled():
    if os.environ.get("ALERT_SCHEDULER_DRY_RUN_ONLY", "false").lower() != "true":
        raise HTTPException(status_code=400, detail="Refusing to start: ALERT_SCHEDULER_DRY_RUN_ONLY must be true.")
    if os.environ.get("ENABLE_ALERT_SCHEDULER", "false").lower() != "true":
        raise HTTPException(status_code=400, detail="Scheduler is disabled in .env (ENABLE_ALERT_SCHEDULER).")
    if not os.environ.get("WEBAPP_TELEGRAM_BOT_TOKEN") or not os.environ.get("WEBAPP_TELEGRAM_CHAT_ID"):
        raise HTTPException(status_code=400, detail="Telegram credentials missing. Check bot token and chat ID.")

async def send_dry_run_alert(forced=False):
    global LAST_RUN_AT, TOTAL_DRY_RUN_SENT
    
    assert_db_allowed()
    bot_token = os.environ.get("WEBAPP_TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("WEBAPP_TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.error("Missing WebApp Telegram Token or Chat ID.")
        return False, "Missing credentials"
        
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    masked_chat = f"***{str(chat_id)[-4:]}" if len(str(chat_id)) > 4 else "***"
    msg_type = "Immediate" if forced else "Scheduled"
    text_content = f"GHBS TASI Web App {msg_type} Dry-Run Alert\nSandbox Time: {current_time}\nThis is a scheduled dry-run check."
    
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

            import aiosqlite
            async with aiosqlite.connect(get_db_path()) as db:
                if data.get("ok"):
                    LAST_RUN_AT = current_time
                    TOTAL_DRY_RUN_SENT += 1
                    await log_alert_event(db, "scheduler_dry_run", f"{msg_type} Dry Run", text_content, "SENT", masked_chat, None, current_time)
                    return True, "Success"
                else:
                    await log_alert_event(db, "scheduler_dry_run", f"{msg_type} Dry Run", text_content, "FAILED", masked_chat, None, current_time)
                    return False, data.get("description", "Unknown API error")
    except httpx.HTTPStatusError as e:
        import aiosqlite
        try:
            assert_db_allowed()
            async with aiosqlite.connect(get_db_path()) as db:
                await log_alert_event(db, "scheduler_dry_run", f"{msg_type} Dry Run", text_content, "FAILED", masked_chat, None, current_time)
        except Exception:
            pass
        return False, "Telegram delivery failed. Check bot token, chat ID, or bot access."
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        import aiosqlite
        try:
            assert_db_allowed()
            async with aiosqlite.connect(get_db_path()) as db:
                await log_alert_event(db, "scheduler_dry_run", f"{msg_type} Dry Run", text_content, "FAILED", masked_chat, None, current_time)
        except Exception:
            pass
        return False, "Telegram delivery failed. Check bot token, chat ID, or bot access."

async def dry_run_loop(interval_seconds: int):
    global NEXT_RUN_ESTIMATE
    while not SCHEDULER_STOP_EVENT.is_set():
        await send_dry_run_alert(forced=False)
        try:
            from datetime import timedelta
            NEXT_RUN_ESTIMATE = (datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
            await asyncio.wait_for(SCHEDULER_STOP_EVENT.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass

@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(current_user: dict = Depends(get_current_user)):
    global SCHEDULER_TASK, LAST_RUN_AT, NEXT_RUN_ESTIMATE, TOTAL_DRY_RUN_SENT
    enabled = os.environ.get("ENABLE_ALERT_SCHEDULER", "false").lower() == "true"
    dry_run = os.environ.get("ALERT_SCHEDULER_DRY_RUN_ONLY", "false").lower() == "true"
    interval = int(os.environ.get("ALERT_TEST_INTERVAL_SECONDS", "300"))
    
    is_running = SCHEDULER_TASK is not None and not SCHEDULER_TASK.done()
    
    has_creds = bool(os.environ.get("WEBAPP_TELEGRAM_BOT_TOKEN") and os.environ.get("WEBAPP_TELEGRAM_CHAT_ID"))
    safety_state = "SAFE" if (enabled and dry_run and has_creds) else "UNSAFE"
    if safety_state == "UNSAFE" and is_running:
        safety_state = "WARNING_UNSAFE_RUNNING"
    
    return SchedulerStatusResponse(
        enabled_in_env=enabled,
        dry_run_only_env=dry_run,
        is_running=is_running,
        interval_seconds=interval,
        last_run_at=LAST_RUN_AT,
        next_run_estimate=NEXT_RUN_ESTIMATE if is_running else None,
        total_dry_run_sent=TOTAL_DRY_RUN_SENT,
        safety_state=safety_state
    )

@router.post("/send-dry-run-now", response_model=SchedulerActionResponse)
async def send_dry_run_now(current_user: dict = Depends(get_current_user)):
    # Requires API smoke tests or scheduler enabled
    smoke_enabled = os.environ.get("ENABLE_API_SMOKE_TESTS", "false").lower() == "true"
    sched_enabled = os.environ.get("ENABLE_ALERT_SCHEDULER", "false").lower() == "true"
    if not (smoke_enabled or sched_enabled):
         raise HTTPException(status_code=400, detail="Smoke tests or scheduler must be enabled.")
         
    success, msg = await send_dry_run_alert(forced=True)
    if success:
        return SchedulerActionResponse(success=True, message="Dry run alert sent successfully.", status="sent")
    else:
        raise HTTPException(status_code=400, detail=msg)

@router.post("/start-dry-run", response_model=SchedulerActionResponse)
async def start_dry_run(current_user: dict = Depends(get_current_user)):
    global SCHEDULER_TASK, SCHEDULER_STOP_EVENT
    assert_scheduler_enabled()
    
    if SCHEDULER_TASK is not None and not SCHEDULER_TASK.done():
        return SchedulerActionResponse(success=True, message="Scheduler is already running.", status="running")
        
    interval = int(os.environ.get("ALERT_TEST_INTERVAL_SECONDS", "300"))
    SCHEDULER_STOP_EVENT.clear()
    SCHEDULER_TASK = asyncio.create_task(dry_run_loop(interval))
    
    return SchedulerActionResponse(success=True, message=f"Dry run scheduler started (interval {interval}s).", status="started")

@router.post("/stop-all", response_model=SchedulerActionResponse)
async def stop_all(current_user: dict = Depends(get_current_user)):
    global SCHEDULER_TASK, SCHEDULER_STOP_EVENT
    
    if SCHEDULER_TASK is not None and not SCHEDULER_TASK.done():
        SCHEDULER_STOP_EVENT.set()
        SCHEDULER_TASK.cancel()
        SCHEDULER_TASK = None
        return SchedulerActionResponse(success=True, message="All dry run scheduler tasks stopped.", status="stopped")
        
    return SchedulerActionResponse(success=True, message="No scheduler tasks were running.", status="stopped")
