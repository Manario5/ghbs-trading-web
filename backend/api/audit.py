from fastapi import APIRouter, Depends
import aiosqlite
from typing import List

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/events")
async def get_audit_events(
    limit: int = 50,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute("""
        SELECT * FROM audit_events 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,)) as cur:
        rows = await cur.fetchall()
        
    return [dict(r) for r in rows]
