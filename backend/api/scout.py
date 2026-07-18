from fastapi import APIRouter, Depends
import os

from backend.auth.dependencies import get_current_user
from backend.services.engine_service import scout_sandbox
from backend.core.execution_guard import verify_no_execution_side_effects

router = APIRouter()


@router.post("/run")
async def run_scout(
    current_user: dict = Depends(get_current_user),
):
    verify_no_execution_side_effects()

    limit = int(os.environ.get("LIVE_SCOUT_LIMIT", "10"))
    res = await scout_sandbox(limit=limit)
    return res
