from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from datetime import datetime
from ..db.database import get_db
from backend.auth.dependencies import get_current_user
from ..models.schemas import ActionPlanCreate, ActionPlanItem

router = APIRouter()

@router.post("", response_model=ActionPlanItem)
async def create_action_plan(
    item: ActionPlanCreate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    now = datetime.utcnow().isoformat()
    async with db.execute(
        """
        INSERT INTO action_plan (ticker, action_type, planned_price, planned_quantity, notes, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """,
        (item.ticker, item.action_type, item.planned_price, item.planned_quantity, item.notes, now)
    ) as cur:
        new_id = cur.lastrowid
        await db.commit()
    
    return {
        **item.dict(),
        "id": new_id,
        "status": "pending",
        "created_at": now
    }

@router.get("/tomorrow")
async def get_action_plan_tomorrow(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute(
        "SELECT * FROM action_plan WHERE status = 'pending' ORDER BY created_at DESC"
    ) as cur:
        rows = await cur.fetchall()
        
    return [dict(r) for r in rows]

@router.patch("/{id}")
async def update_action_plan(
    id: int,
    status: str,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute("UPDATE action_plan SET status = ? WHERE id = ?", (status, id)) as cur:
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        await db.commit()
    return {"message": "Updated successfully"}

@router.delete("/{id}")
async def delete_action_plan(
    id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute("DELETE FROM action_plan WHERE id = ?", (id,)) as cur:
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        await db.commit()
    return {"message": "Deleted successfully"}
