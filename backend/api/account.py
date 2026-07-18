from fastapi import APIRouter, Depends
import aiosqlite

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.schemas import AccountSummary
from backend.core.config import CFG

router = APIRouter()

@router.get("/summary", response_model=AccountSummary)
async def get_account_summary(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute("SELECT value FROM system_state WHERE key='current_equity'") as cur:
        row = await cur.fetchone()
        equity_val = float(row["value"]) if row else CFG.initial_equity_sar

    async with db.execute("""
        SELECT
            COUNT(*) AS total_trades,
            SUM(CASE WHEN realized_pnl_sar > 0 THEN 1 ELSE 0 END) AS winners,
            SUM(realized_pnl_sar) AS total_pnl
        FROM positions WHERE position_state='CLOSED'
    """) as cur:
        stats = await cur.fetchone()
        
    total_trades = stats["total_trades"] or 0
    winners = stats["winners"] or 0
    total_pnl = stats["total_pnl"] or 0.0
    win_rate = (winners / total_trades * 100) if total_trades > 0 else 0.0

    return {
        "starting_equity": CFG.initial_equity_sar,
        "current_equity": equity_val,
        "net_pnl": total_pnl,
        "win_rate": win_rate,
        "total_trades": total_trades
    }
