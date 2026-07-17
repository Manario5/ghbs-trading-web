from fastapi import APIRouter, Depends, HTTPException
import aiosqlite
from datetime import datetime
from ..db.database import get_db
from backend.auth.dependencies import get_current_user
from ..models.schemas import JournalCreate, JournalEntry

router = APIRouter()

@router.post("", response_model=JournalEntry)
async def create_journal_entry(
    entry: JournalCreate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    now = datetime.utcnow().isoformat()
    async with db.execute(
        """
        INSERT INTO journal_entries (ticker, position_id, transaction_id, note_type, note_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (entry.ticker, entry.position_id, entry.transaction_id, entry.note_type, entry.note_text, now)
    ) as cur:
        new_id = cur.lastrowid
        await db.commit()
    
    return {
        **entry.dict(),
        "id": new_id,
        "created_at": now
    }

@router.get("")
async def get_all_journal_entries(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute("SELECT * FROM journal_entries ORDER BY created_at DESC") as cur:
        rows = await cur.fetchall()
        
    return [dict(r) for r in rows]

@router.get("/{ticker}")
async def get_journal_entries_by_ticker(
    ticker: str,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute("SELECT * FROM journal_entries WHERE ticker = ? ORDER BY created_at DESC", (ticker,)) as cur:
        rows = await cur.fetchall()
        
    return [dict(r) for r in rows]
