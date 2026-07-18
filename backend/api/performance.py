from fastapi import APIRouter, Depends
import aiosqlite
from typing import List, Dict, Any

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.schemas import PerformanceSummary

router = APIRouter()

@router.get("/summary", response_model=PerformanceSummary)
async def get_performance_summary(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    async with db.execute("""
        SELECT
            COUNT(*) AS total_trades,
            SUM(CASE WHEN realized_pnl_sar > 0 THEN 1 ELSE 0 END) AS winners,
            SUM(realized_pnl_sar) AS total_pnl
        FROM positions WHERE position_state='CLOSED'
    """) as cur:
        pos_stats = await cur.fetchone()

    async with db.execute("""
        SELECT
            AVG(r_multiple) AS avg_r,
            MAX(r_multiple) AS best_r,
            MIN(r_multiple) AS worst_r
        FROM transactions
        WHERE transaction_type IN ('SELL','PARTIAL_SELL')
          AND r_multiple IS NOT NULL
    """) as cur:
        tx_stats = await cur.fetchone()

    return {
        "total_trades": pos_stats["total_trades"] or 0,
        "winners": pos_stats["winners"] or 0,
        "total_pnl": pos_stats["total_pnl"] or 0.0,
        "avg_r": tx_stats["avg_r"],
        "best_r": tx_stats["best_r"],
        "worst_r": tx_stats["worst_r"]
    }
