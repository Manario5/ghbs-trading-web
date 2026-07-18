from fastapi import APIRouter, Depends
import aiosqlite
from typing import List, Dict, Any

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/open")
async def get_open_positions(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute("SELECT * FROM positions WHERE position_state!='CLOSED' ORDER BY opened_at DESC") as cur:
        rows = await cur.fetchall()
        
    return [dict(r) for r in rows]
