from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.auth.dependencies import get_current_user
from backend.services.engine_service import can_i_take_this_trade
from backend.db.database import get_db_path, assert_db_allowed

router = APIRouter()

class RiskCalcRequest(BaseModel):
    ticker: str
    entry_price: float
    qty: int

@router.post("/can-i-take-this-trade")
async def can_i_take_trade(
    req: RiskCalcRequest,
    current_user: dict = Depends(get_current_user)
):
    assert_db_allowed()
    db_path = get_db_path()
    res = await can_i_take_this_trade(db_path, req.ticker.upper(), req.entry_price, req.qty)
    return res
