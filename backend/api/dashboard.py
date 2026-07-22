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


# ── Read-only dashboard chart / summary endpoints (Private Live Command Center) ──
# All endpoints below are strictly read-only over existing SQLite tables. They
# never call external providers, never run the engine, and never write data.
# When a table is empty they return empty arrays plus an explanatory message.

_REGIME_SCORE = {
    "STRONG_BULL": 2, "BULL": 1, "GREEN": 1, "UP": 1,
    "NEUTRAL": 0, "MIXED": 0, "FLAT": 0,
    "BEAR": -1, "RED": -1, "DOWN": -1, "STRONG_BEAR": -2,
}


async def _fetchall(db, sql, params=()):
    try:
        async with db.execute(sql, params) as cur:
            return [dict(r) for r in await cur.fetchall()]
    except Exception:
        return []


@router.get("/provider-health")
async def dashboard_provider_health(current_user: dict = Depends(get_current_user)):
    """Provider readiness + fallback (read-only, config-only)."""
    from backend.core.provider_health import get_provider_health
    return get_provider_health()


@router.get("/scout-funnel")
async def dashboard_scout_funnel(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    rows = await _fetchall(
        db,
        "SELECT * FROM live_preview_runs WHERE preview_type='scout' ORDER BY id DESC LIMIT 1",
    )
    if not rows:
        return {"available": False, "message": "No scout preview runs recorded yet.", "stages": []}
    r = rows[0]
    scanned = r.get("scanned_count", 0) or 0
    eligible = r.get("eligible_count", 0) or 0
    blocked = r.get("blocked_count", 0) or 0
    failures = r.get("data_failures", 0) or 0
    top = max(eligible - blocked, 0)
    return {
        "available": True,
        "message": "",
        "as_of": r.get("created_at"),
        "provider": r.get("provider"),
        "stages": [
            {"stage": "Universe scanned", "count": scanned},
            {"stage": "Eligible", "count": eligible},
            {"stage": "Blocked", "count": blocked},
            {"stage": "Data failures", "count": failures},
            {"stage": "Top candidates", "count": top},
        ],
    }


@router.get("/alert-activity")
async def dashboard_alert_activity(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    rows = await _fetchall(
        db,
        """
        SELECT substr(created_at,1,10) AS day, alert_type, delivery_status, COUNT(*) AS n
        FROM alert_events
        GROUP BY day, alert_type, delivery_status
        ORDER BY day ASC
        """,
    )
    if not rows:
        return {"available": False, "message": "No alert activity recorded yet.", "series": [], "totals": {}}

    by_day: dict = {}
    totals = {"manual": 0, "scheduled": 0, "sent": 0, "failed": 0}
    for r in rows:
        day = r["day"]
        n = r["n"]
        atype = (r.get("alert_type") or "").lower()
        is_sched = "sched" in atype
        is_sent = str(r.get("delivery_status", "")).upper().startswith("SENT")
        entry = by_day.setdefault(day, {"day": day, "manual": 0, "scheduled": 0, "sent": 0, "failed": 0})
        entry["scheduled" if is_sched else "manual"] += n
        entry["sent" if is_sent else "failed"] += n
        totals["scheduled" if is_sched else "manual"] += n
        totals["sent" if is_sent else "failed"] += n

    return {"available": True, "message": "", "series": list(by_day.values()), "totals": totals}


@router.get("/charts")
async def dashboard_charts(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # 1) Market regime trend from setup_log.market_regime over time
    regime_rows = await _fetchall(
        db,
        """
        SELECT substr(logged_at,1,10) AS day, market_regime
        FROM setup_log
        WHERE market_regime IS NOT NULL AND market_regime != ''
        ORDER BY logged_at ASC
        """,
    )
    regime_by_day: dict = {}
    for r in regime_rows:
        score = _REGIME_SCORE.get(str(r["market_regime"]).upper().strip(), 0)
        regime_by_day.setdefault(r["day"], []).append(score)
    regime_trend = [
        {"day": d, "score": round(sum(v) / len(v), 3)} for d, v in regime_by_day.items()
    ]

    # 2) Setup signal distribution
    setup_rows = await _fetchall(
        db,
        "SELECT COALESCE(setup_type,'NONE') AS setup_type, COUNT(*) AS n FROM setup_log GROUP BY setup_type",
    )
    setup_distribution = [{"setup_type": r["setup_type"], "count": r["n"]} for r in setup_rows]

    # 3) Symbol strength ranking (avg confidence per ticker)
    symbol_rows = await _fetchall(
        db,
        """
        SELECT ticker, COUNT(*) AS n, AVG(COALESCE(confidence,0)) AS avg_conf
        FROM setup_log
        GROUP BY ticker
        ORDER BY avg_conf DESC, n DESC
        LIMIT 10
        """,
    )
    symbol_strength = [
        {"ticker": r["ticker"], "score": round(float(r["avg_conf"] or 0), 1), "samples": r["n"]}
        for r in symbol_rows
    ]

    # 4) Live preview outcomes
    preview_rows = await _fetchall(
        db,
        "SELECT preview_type, COUNT(*) AS n FROM live_preview_runs GROUP BY preview_type",
    )
    preview_counts = {r["preview_type"]: r["n"] for r in preview_rows}
    alert_total_rows = await _fetchall(db, "SELECT COUNT(*) AS n FROM alert_events")
    alerts_generated = alert_total_rows[0]["n"] if alert_total_rows else 0
    live_preview_outcomes = [
        {"label": "Analyze previews", "count": preview_counts.get("analyze", 0)},
        {"label": "Scout previews", "count": preview_counts.get("scout", 0)},
        {"label": "Alerts generated", "count": alerts_generated},
        {"label": "Trade executions", "count": 0},  # always 0 — execution is impossible
    ]

    return {
        "regime_trend": {
            "available": bool(regime_trend),
            "message": "" if regime_trend else "No regime history yet.",
            "points": regime_trend,
        },
        "setup_distribution": {
            "available": bool(setup_distribution),
            "message": "" if setup_distribution else "No setup signals recorded yet.",
            "items": setup_distribution,
        },
        "symbol_strength": {
            "available": bool(symbol_strength),
            "message": "" if symbol_strength else "No symbol data yet.",
            "items": symbol_strength,
        },
        "live_preview_outcomes": {
            "available": True,
            "message": "",
            "items": live_preview_outcomes,
        },
    }


@router.get("/live-summary")
async def dashboard_live_summary(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Aggregated read-only snapshot for the Live Operations panel."""
    from backend.db.database import get_db_path
    from backend.core.execution_guard import get_execution_guard_status
    from backend.core.operating_mode import get_operating_mode

    exec_active = any(get_execution_guard_status().values())
    mode = get_operating_mode(get_db_path(), exec_active)

    # Risk / exposure snapshot
    async with db.execute("SELECT value FROM system_state WHERE key='current_equity'") as cur:
        row = await cur.fetchone()
        equity_val = float(row["value"]) if row else float(CFG.initial_equity_sar)
    open_positions = (await _fetchall(
        db, "SELECT COUNT(*) AS n FROM positions WHERE position_state!='CLOSED'"))
    open_count = open_positions[0]["n"] if open_positions else 0
    heat_rows = await _fetchall(
        db, "SELECT COALESCE(SUM(initial_risk_sar),0) AS heat FROM positions WHERE position_state!='CLOSED'")
    heat = float(heat_rows[0]["heat"]) if heat_rows else 0.0

    last_alert = await _fetchall(
        db, "SELECT alert_type, delivery_status, destination_masked, created_at FROM alert_events ORDER BY id DESC LIMIT 1")
    last_analyze = await _fetchall(
        db, "SELECT created_at, provider, requested_ticker FROM live_preview_runs WHERE preview_type='analyze' ORDER BY id DESC LIMIT 1")
    last_scout = await _fetchall(
        db, "SELECT created_at, provider, scanned_count FROM live_preview_runs WHERE preview_type='scout' ORDER BY id DESC LIMIT 1")

    return {
        "operating_mode": mode["mode"],
        "operating_mode_label": mode["mode_label"],
        "telegram_sending_active": mode["telegram_sending_active"],
        "scheduler_enabled": mode["automation"]["scheduler_enabled"],
        "live_preview_read_only": mode["live_preview_read_only"],
        "production_db_write_possible": mode["production_db_write_possible"],
        "trade_execution_possible": mode["trade_execution_possible"],
        "risk_snapshot": {
            "equity": equity_val,
            "open_positions": open_count,
            "portfolio_heat_pct": round(heat / equity_val * 100, 2) if equity_val else 0.0,
            "exposure_pct": None,  # not tracked without live marks — empty state
        },
        "last_alert": last_alert[0] if last_alert else None,
        "last_analyze_preview": last_analyze[0] if last_analyze else None,
        "last_scout_preview": last_scout[0] if last_scout else None,
    }
