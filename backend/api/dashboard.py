from fastapi import APIRouter, Depends
import aiosqlite

from backend.db.database import get_db, get_db_path
from backend.auth.dependencies import get_current_user
from backend.models.schemas import DashboardSummary
from backend.core.executor import get_equity
from backend.core.config import CFG

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    equity = await get_equity(get_db_path())
    
    # We will use the injected db object to query values.
    # We should override get_equity to use the passed db object.
    async with db.execute("SELECT value FROM system_state WHERE key='current_equity'") as cur:
        row = await cur.fetchone()
        equity_val = float(row["value"]) if row else CFG.initial_equity_sar

    async with db.execute("SELECT COUNT(*) AS open_count FROM positions WHERE position_state!='CLOSED'") as cur:
        row = await cur.fetchone()
        open_positions = row["open_count"] if row else 0

    async with db.execute("SELECT COALESCE(SUM(initial_risk_sar),0) AS total_risk FROM positions WHERE position_state!='CLOSED'") as cur:
        row = await cur.fetchone()
        heat = float(row["total_risk"]) if row else 0.0

    return {
        "equity": equity_val,
        "open_positions": open_positions,
        "portfolio_heat": heat,
        "regime": "NEUTRAL" # Real regime requires fetching standard universe. For MVP 2A, return "NEUTRAL"
    }
