from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from backend.auth.dependencies import get_current_user
from backend.services.engine_service import buy_sandbox, sell_sandbox
from backend.db.database import get_db_path, assert_db_allowed

router = APIRouter()

class BuyRequest(BaseModel):
    ticker: str
    price: float
    qty: int

class SellRequest(BaseModel):
    ticker: str
    price: float
    qty: Optional[int] = None

@router.post("/buy")
async def trade_buy(
    req: BuyRequest,
    current_user: dict = Depends(get_current_user)
):
    assert_db_allowed()
    db_path = get_db_path()
    res = await buy_sandbox(db_path, current_user["id"], req.ticker.upper(), req.price, req.qty)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.post("/sell")
async def trade_sell(
    req: SellRequest,
    current_user: dict = Depends(get_current_user)
):
    assert_db_allowed()
    db_path = get_db_path()
    res = await sell_sandbox(db_path, current_user["id"], req.ticker.upper(), req.price, req.qty)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res
