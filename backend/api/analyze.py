from fastapi import APIRouter, Depends
from typing import Optional

from backend.auth.dependencies import get_current_user
from backend.services.engine_service import analyze_sandbox
from backend.db.database import get_db_path, assert_db_allowed
from backend.core.execution_guard import verify_no_execution_side_effects

router = APIRouter()


@router.post("/{ticker}")
async def analyze_ticker(
    ticker: str,
    risk_pct: Optional[float] = None,
    current_user: dict = Depends(get_current_user),
):
    assert_db_allowed()
    verify_no_execution_side_effects()

    db_path = get_db_path()
    res = await analyze_sandbox(ticker.upper(), risk_pct, db_path)
    return res
