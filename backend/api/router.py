from fastapi import APIRouter

from backend.api import auth
from backend.api import system
from backend.api import dashboard
from backend.api import account
from backend.api import positions
from backend.api import performance
from backend.api import setups
from backend.api import history
from backend.api import audit
from backend.api import analyze
from backend.api import scout
from backend.api import trades
from backend.api import risk
from backend.api import action_plan
from backend.api import journal
from backend.api import integrations
from backend.api import alerts
from backend.api import scheduler
from backend.api import market_data
from backend.api import live_preview

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(account.router, prefix="/account", tags=["Account"])
api_router.include_router(positions.router, prefix="/positions", tags=["Positions"])
api_router.include_router(performance.router, prefix="/performance", tags=["Performance"])
api_router.include_router(setups.router, prefix="/setups", tags=["Setups"])
api_router.include_router(history.router, prefix="/history", tags=["History"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["Analyze"])
api_router.include_router(scout.router, prefix="/scout", tags=["Scout"])
api_router.include_router(trades.router, prefix="/trades", tags=["Trades"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk"])
api_router.include_router(action_plan.router, prefix="/action-plan", tags=["Action Plan"])
api_router.include_router(journal.router, prefix="/journal", tags=["Journal"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["Integrations"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["Scheduler"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["Market Data"])
api_router.include_router(live_preview.router, prefix="/live-preview", tags=["Live Preview"])
