import uuid
import datetime
import aiosqlite
from typing import Dict, Any, Optional

from backend.core.config import CFG
from backend.core.universe import TIER_MAP, SECTOR_MAP, WATCHLIST
from backend.core.classifier import classify_setup
from backend.core.regime import compute_regime, get_sector_breadth
from backend.core.sizes import SizingEngine, SizeProposal
from backend.core.executor import TradeExecutor, get_equity, _now_iso

# Mock data generator for sandbox mode
def get_mock_stock_data(ticker: str) -> Dict[str, Any]:
    # Creating a dummy stock payload that mimics a real response
    # to trigger setups arbitrarily. 
    return {
        "ticker": ticker,
        "close": 50.0,
        "open": 49.0,
        "change_pct": 2.04,
        "volume": 1000000,
        "vol_surge": 2.5,
        "rsi": 75.0, # overbought -> breakout
        "macd": 0.5,
        "macd_signal": 0.2,
        "macd_hist": 0.3,
        "macd_hist_prev": 0.1,
        "bb_upper": 48.0,
        "bb_lower": 40.0,
        "atr14": 2.0,
        "atr22": 2.2,
        "adx14": 25.0,
        "sma200": 45.0,
        "above_sma200": True,
        "obv_trend": "ACCUMULATION",
        "high": 51.0,
        "low": 48.5,
        "bar_date": datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    }

async def analyze_sandbox(ticker: str, risk_pct: Optional[float] = None, db_path: str = CFG.db_path) -> Dict[str, Any]:
    stock = get_mock_stock_data(ticker)
    market_regime = "NEUTRAL"
    sec_breadth = 0.5
    
    result = classify_setup(stock, market_regime, sec_breadth)
    
    equity = await get_equity(db_path)
    proposal: Optional[SizeProposal] = None
    mock_claude_signal = "BUY" if result["mechanical_actionable"] else "HOLD"
    
    if mock_claude_signal == "BUY":
        prop = SizingEngine.propose(equity, stock["close"], stock["atr22"], risk_pct=risk_pct)
        if not prop.reject_reason:
            proposal = prop
            
    return {
        "ticker": ticker,
        "mocked_data": True,
        "external_api_calls": False,
        "setup_type": result["setup_type"],
        "mechanical_reason": result["mechanical_reason"],
        "market_regime": market_regime,
        "claude_signal_mocked": mock_claude_signal,
        "proposal": {
            "shares": proposal.shares,
            "notional": proposal.notional,
            "stop_price": proposal.stop_price,
            "tp1_price": proposal.tp1_price,
            "tp2_price": proposal.tp2_price,
            "tp3_price": proposal.tp3_price,
            "risk_amount": proposal.risk_amount
        } if proposal else None
    }


async def scout_sandbox(limit: int = 10) -> Dict[str, Any]:
    subset = WATCHLIST[:limit]
    all_stocks = [get_mock_stock_data(t) for t in subset]
    
    regime_data = compute_regime(all_stocks)
    market_regime = regime_data["regime"]
    
    actionable_count = 0
    blocked_count = 0
    
    results = []
    
    for stock in all_stocks:
        ticker = stock["ticker"]
        sec_breadth = get_sector_breadth(ticker, regime_data)
        result = classify_setup(stock, market_regime, sec_breadth)
        if result["mechanical_actionable"]:
            actionable_count += 1
        else:
            blocked_count += 1
            
        results.append({
            "ticker": ticker,
            "setup_type": result["setup_type"],
            "actionable": result["mechanical_actionable"] == 1
        })
        
    return {
        "mocked_data": True,
        "external_api_calls": False,
        "fetched": len(subset),
        "failed": 0,
        "actionable": actionable_count,
        "blocked": blocked_count,
        "regime": market_regime,
        "results": results
    }

async def record_audit_event(db_path: str, user_id: int, action_type: str, object_type: str, object_id: str, notes: str):
    from backend.db.database import assert_db_allowed
    assert_db_allowed()
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO audit_events (user_id, action_type, object_type, object_id, timestamp, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, action_type, object_type, object_id, _now_iso(), notes))
        await db.commit()

async def buy_sandbox(db_path: str, user_id: int, ticker: str, price: float, qty: int) -> Dict[str, Any]:
    executor = TradeExecutor(db_path=db_path)
    sig_id = str(uuid.uuid4())
    sig_time = datetime.datetime.now(datetime.timezone.utc)
    
    stock = get_mock_stock_data(ticker)
    atr = stock["atr22"]
    
    res = await executor.record_buy(ticker, price, qty, sig_id, sig_time, atr=atr)
    
    if res.success:
        await record_audit_event(db_path, user_id, "SANDBOX_BUY", "position", str(res.position_id), f"Bought {qty} {ticker} @ {price}")
        
    return {
        "sandbox_mode": True,
        "success": res.success,
        "message": res.message,
        "position_id": res.position_id
    }

async def sell_sandbox(db_path: str, user_id: int, ticker: str, price: float, qty: Optional[int]) -> Dict[str, Any]:
    executor = TradeExecutor(db_path=db_path)
    sig_id = str(uuid.uuid4())
    sig_time = datetime.datetime.now(datetime.timezone.utc)
    
    res = await executor.record_sell(ticker, price, qty, sig_id, sig_time, reason="MANUAL")
    
    if res.success:
        await record_audit_event(db_path, user_id, "SANDBOX_SELL", "position", str(res.position_id), f"Sold {qty or 'ALL'} {ticker} @ {price}")
        
    return {
        "sandbox_mode": True,
        "success": res.success,
        "message": res.message,
        "position_id": res.position_id
    }

async def can_i_take_this_trade(db_path: str, ticker: str, entry_price: float, qty: int) -> Dict[str, Any]:
    stock = get_mock_stock_data(ticker)
    atr = stock["atr22"]
    
    equity = await get_equity(db_path)
    pass_fail = True
    warnings = []
    
    stop_dist = atr * CFG.stop_atr_multiple
    risk_amount = stop_dist * qty
    risk_pct = risk_amount / equity if equity else 0.0
    notional = qty * entry_price
    notional_pct = notional / equity if equity else 0.0
    
    if risk_pct > CFG.risk_per_trade_pct:
        pass_fail = False
        warnings.append(f"Risk {risk_pct*100:.2f}% exceeds {CFG.risk_per_trade_pct*100:.2f}% cap.")
        
    if notional_pct > CFG.max_notional_pct:
        pass_fail = False
        warnings.append(f"Notional {notional_pct*100:.2f}% exceeds {CFG.max_notional_pct*100:.2f}% cap.")
        
    from backend.db.database import assert_db_allowed
    assert_db_allowed()

    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT COALESCE(SUM(initial_risk_sar),0) FROM positions WHERE position_state!='CLOSED'") as cur:
            row = await cur.fetchone()
            current_heat = float(row[0]) if row else 0.0
            
    heat_estimate = current_heat + risk_amount
    heat_pct = heat_estimate / equity if equity else 0.0
    if heat_pct > CFG.max_portfolio_heat:
        pass_fail = False
        warnings.append(f"Portfolio heat {heat_pct*100:.2f}% exceeds {CFG.max_portfolio_heat*100:.2f}% cap.")

    tp1_price = entry_price + (stop_dist * CFG.tp1_r_multiple)
    tp2_price = entry_price + (stop_dist * CFG.tp2_r_multiple)
    tp3_price = entry_price + (stop_dist * CFG.tp3_r_multiple)
    stop_price = entry_price - stop_dist
    
    return {
        "sandbox_mode": True,
        "entry_price": entry_price,
        "qty": qty,
        "atr_used": atr,
        "risk_sar": risk_amount,
        "risk_pct": risk_pct * 100,
        "notional_sar": notional,
        "notional_pct": notional_pct * 100,
        "heat_estimate_sar": heat_estimate,
        "heat_estimate_pct": heat_pct * 100,
        "stop_price": stop_price,
        "tp1": tp1_price,
        "tp2": tp2_price,
        "tp3": tp3_price,
        "pass": pass_fail,
        "warnings": warnings
    }
