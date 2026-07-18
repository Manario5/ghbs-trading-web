import asyncio
import pytest
from datetime import datetime, timezone
import aiosqlite

from backend.core.universe import TIER_MAP, SECTOR_MAP
from backend.core.config import CFG
from backend.core.classifier import classify_setup
from backend.core.regime import compute_regime
from backend.core.sizes import SizingEngine
from backend.core.chandelier import ChandelierEngine
from backend.core.executor import TradeExecutor

@pytest.fixture
def mock_stock_data():
    return {
        "ticker": "2222",
        "close": 35.0,
        "open": 34.5,
        "rsi": 30.0,
        "bb_lower": 36.0,
        "bb_upper": 40.0,
        "vol_surge": 1.2,
        "adx14": 25.0,
        "macd_hist": -0.05,
        "macd_hist_prev": -0.1,
        "above_sma200": True
    }

@pytest.mark.asyncio
async def test_classify_setup_bounce(mock_stock_data):
    # Oversold RSI AND improving MACD -> BOUNCE
    res = classify_setup(mock_stock_data, "BULLISH", 0.6)
    assert res["setup_type"] == "BOUNCE_SETUP"
    assert res["mechanical_actionable"] == 1
    assert "MACD_IMPROVING" in res["mechanical_reason"]

@pytest.mark.asyncio
async def test_compute_regime():
    stocks = [
        {"ticker": "1120", "above_sma200": True},
        {"ticker": "2222", "above_sma200": True},
        {"ticker": "1180", "above_sma200": False},
        {"ticker": "7202", "above_sma200": False},
        {"ticker": "6004", "above_sma200": True},
    ]
    regime_data = compute_regime(stocks)
    # 3/5 = 60%, so BULLISH
    assert regime_data["regime"] == "BULLISH"
    assert regime_data["market_breadth"] == 0.6
    assert "TIER_1" in regime_data["tier_breadth"]

@pytest.mark.asyncio
async def test_sizing_engine():
    equity = 100_000.0
    price = 50.0
    atr = 2.0
    # Stop distance = 2.0 * 2.5 = 5.0
    # Risk budget = 100,000 * 0.01 = 1,000
    # Shares = 1000 / 5.0 = 200
    prop = SizingEngine.propose(equity, price, atr)
    assert prop.shares == 200
    assert prop.stop_price == 45.0
    assert prop.tp1_price == 55.0  # entry + 1R
    assert prop.tp2_price == 60.0  # entry + 2R
    assert prop.tp3_price == 65.0  # entry + 3R

@pytest.mark.asyncio
async def test_chandelier_engine():
    pos_row = {
        "highest_close_since_entry": 50.0,
        "stop_atr_multiple": 2.5
    }
    data = {"close": 51.0, "low": 49.0, "atr22": 2.0}
    # New watermark = 51.0
    # stop = 51.0 - 5.0 = 46.0
    # Since low 49.0 > 46.0 -> NEW_HIGH
    res = ChandelierEngine.evaluate(pos_row, data)
    assert res.kind == "NEW_HIGH"
    assert res.stop_level == 46.0
    assert res.watermark == 51.0

@pytest.mark.asyncio
async def test_trade_executor(tmp_path):
    db_path = str(tmp_path / "test.db")
    async with aiosqlite.connect(db_path) as db:
        await db.executescript("""
            CREATE TABLE system_state (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);
            INSERT INTO system_state VALUES ('current_equity', '100000', 'now');
            CREATE TABLE positions (
                id INTEGER PRIMARY KEY, ticker TEXT, position_state TEXT, opened_at TEXT, closed_at TEXT,
                initial_entry_price REAL, avg_cost REAL, initial_atr REAL, original_position_size INTEGER,
                current_position_size INTEGER, highest_close_since_entry REAL, stop_atr_multiple REAL, 
                risk_per_trade_pct REAL, total_commissions_sar REAL, initial_risk_sar REAL, take_profit_price REAL,
                tp1_price REAL, tp2_price REAL, tp3_price REAL, tp1_hit INTEGER, version INTEGER, 
                partial_exit_taken INTEGER DEFAULT 0, last_stop_alert_date TEXT, exit_reason TEXT, 
                realized_pnl_sar REAL DEFAULT 0, notes TEXT
            );
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY, position_id INTEGER, ticker TEXT, transaction_type TEXT, 
                signal_time TEXT, execution_time TEXT, fill_price REAL, quantity INTEGER, commission_sar REAL,
                reason_code TEXT, equity_snapshot REAL, realized_pnl_sar REAL DEFAULT 0, r_multiple REAL,
                duration_days REAL, roi_pct REAL, modeled_risk_sar REAL, realized_risk_sar REAL, slippage_sar REAL, notes TEXT
            );
            CREATE TABLE signal_events (
                signal_id TEXT, position_id INTEGER, trade_date TEXT, reason_code TEXT, generated_at TEXT, event_source TEXT
            );
            CREATE TABLE setup_log (
                id INTEGER PRIMARY KEY, logged_at TEXT, ticker TEXT, setup_type TEXT, mechanical_actionable INTEGER,
                mechanical_reason TEXT, market_regime TEXT, sector TEXT, sector_breadth REAL, claude_signal TEXT,
                confidence INTEGER, adx REAL, rsi REAL, obv_trend TEXT, vol_surge REAL, entry_taken INTEGER DEFAULT 0,
                position_id INTEGER, outcome_r REAL, tier TEXT, notes TEXT
            );
            INSERT INTO setup_log (ticker, claude_signal, entry_taken, logged_at) VALUES ('2222', 'BUY', 0, 'now');
        """)
        await db.commit()

    executor = TradeExecutor(db_path)
    res_buy = await executor.record_buy("2222", 50.0, 100, "sig_1", datetime.now(timezone.utc), atr=2.0)
    assert res_buy.success

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM positions WHERE id=?", (res_buy.position_id,)) as cur:
            pos = await cur.fetchone()
            assert pos["current_position_size"] == 100
            assert pos["avg_cost"] > 50.0  # cost + commission
            assert pos["initial_risk_sar"] == 500.0  # 100 * (2*2.5)

    res_sell = await executor.record_sell("2222", 55.0, 40, "sig_2", datetime.now(timezone.utc))
    assert res_sell.success
    assert "PARTIAL_SELL" in res_sell.message

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT current_position_size, tp1_hit, position_state FROM positions WHERE id=?", (res_buy.position_id,)) as cur:
            pos = await cur.fetchone()
            assert pos["current_position_size"] == 60
            assert pos["tp1_hit"] == 1
            assert pos["position_state"] == "PARTIAL"
