from fastapi import APIRouter, Depends
import aiosqlite
from typing import List

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/")
async def get_setups(
    limit: int = 20,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute("""
        SELECT * FROM setup_log 
        ORDER BY logged_at DESC 
        LIMIT ?
    """, (limit,)) as cur:
        rows = await cur.fetchall()
        
    return [dict(r) for r in rows]
