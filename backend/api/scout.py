from fastapi import APIRouter, Depends
from backend.auth.dependencies import get_current_user
from backend.services.engine_service import scout_sandbox

router = APIRouter()

@router.post("/run")
async def run_scout(
    current_user: dict = Depends(get_current_user)
):
    res = await scout_sandbox()
    return res
