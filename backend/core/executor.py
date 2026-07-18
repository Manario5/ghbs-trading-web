import asyncio
import aiosqlite
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .config import CFG

@dataclass(slots=True)
class ExecResult:
    success: bool
    message: str
    position_id: Optional[int] = None

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _commission(price: float, qty: int) -> float:
    return round(price * qty * CFG.commission_pct, 2)

async def get_equity(db_path: str) -> float:
    from backend.db.database import assert_db_allowed
    assert_db_allowed()
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT value FROM system_state WHERE key='current_equity'"
        ) as cur:
            row = await cur.fetchone()
    return float(row[0]) if row else CFG.initial_equity_sar

async def with_optimistic_retry(coro_fn, *args, max_retries: int = 3, **kwargs) -> ExecResult:
    for attempt in range(max_retries):
        result = await coro_fn(*args, **kwargs)
        if result.success or "Concurrency conflict" not in result.message:
            return result
        if attempt < max_retries - 1:
            await asyncio.sleep(0.1 * (2 ** attempt))
    return result

class TradeExecutor:
    def __init__(self, db_path: str = CFG.db_path):
        self.db = db_path

    async def record_buy(self, ticker: str, fill_price: float, qty: int,
                         sig_id: str, sig_time: datetime,
                         atr: float) -> ExecResult:
        if fill_price <= 0 or qty <= 0:
            return ExecResult(False, "Price and quantity must be > 0")

        comm              = _commission(fill_price, qty)
        eff_cost          = ((fill_price * qty) + comm) / qty
        stop_dist         = atr * CFG.stop_atr_multiple
        initial_risk_sar  = round(stop_dist * qty, 2)
        stop_price        = round(fill_price - stop_dist, 2)
        tp1_price         = round(fill_price + (stop_dist * CFG.tp1_r_multiple), 2)
        tp2_price         = round(fill_price + (stop_dist * CFG.tp2_r_multiple), 2)
        tp3_price         = round(fill_price + (stop_dist * CFG.tp3_r_multiple), 2)
        take_profit_price = tp2_price 
        equity            = await get_equity(self.db)
        from backend.db.database import assert_db_allowed
        assert_db_allowed()

        async with aiosqlite.connect(self.db) as db:
            db.row_factory = aiosqlite.Row
            try:
                await db.execute("BEGIN IMMEDIATE")

                async with db.execute(
                    "SELECT 1 FROM signal_events WHERE signal_id=?", (sig_id,)
                ) as cur:
                    if await cur.fetchone():
                        await db.rollback()
                        return ExecResult(False, "Command already processed")

                async with db.execute(
                    "SELECT * FROM positions WHERE ticker=? AND position_state!='CLOSED'",
                    (ticker,)
                ) as cur:
                    pos = await cur.fetchone()

                if pos:
                    new_qty  = pos["current_position_size"] + qty
                    new_avg  = ((pos["avg_cost"] * pos["current_position_size"]) +
                                (eff_cost * qty)) / new_qty
                    new_high = max(pos["highest_close_since_entry"], fill_price)
                    upd = await db.execute(
                        """UPDATE positions SET
                               current_position_size=?, avg_cost=?,
                               highest_close_since_entry=?,
                               total_commissions_sar=total_commissions_sar+?,
                               initial_risk_sar=initial_risk_sar+?,
                               version=version+1
                           WHERE id=? AND version=?""",
                        (new_qty, new_avg, new_high, comm,
                         initial_risk_sar, pos["id"], pos["version"])
                    )
                    if upd.rowcount == 0:
                        await db.rollback()
                        return ExecResult(False, "Concurrency conflict — retry")
                    pos_id = pos["id"]
                    msg_out = (
                        f"TOP-UP {ticker}: +{qty} @ {fill_price:.2f}\\n"
                        f"Total: {new_qty} shares @ avg {new_avg:.2f} SAR\\n"
                        f"🛡️ SL: {stop_price:.2f}\\n"
                        f"🎯 TP1: {tp1_price:.2f}  TP2: {tp2_price:.2f}  TP3: {tp3_price:.2f}\\n"
                        f"Fee: {comm:.2f} SAR"
                    )
                else:
                    tp1_qty = math.floor(qty * CFG.tp1_scale_out_pct)
                    tp2_qty = math.floor(qty * CFG.tp2_scale_out_pct)
                    tp3_qty = qty - tp1_qty - tp2_qty

                    cur2 = await db.execute(
                        """INSERT INTO positions(
                               ticker, position_state, opened_at,
                               initial_entry_price, avg_cost, initial_atr,
                               original_position_size, current_position_size,
                               highest_close_since_entry, stop_atr_multiple,
                               risk_per_trade_pct, total_commissions_sar,
                               initial_risk_sar, take_profit_price,
                               tp1_price, tp2_price, tp3_price, tp1_hit, version
                           ) VALUES(?, 'OPEN', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1)""",
                        (ticker, sig_time.isoformat(), fill_price, eff_cost, atr,
                         qty, qty, fill_price, CFG.stop_atr_multiple,
                         CFG.risk_per_trade_pct, comm,
                         initial_risk_sar, take_profit_price,
                         tp1_price, tp2_price, tp3_price)
                    )
                    pos_id = cur2.lastrowid
                    stop_pct = (stop_dist / fill_price) * 100
                    tp1_pct  = ((tp1_price - fill_price) / fill_price) * 100
                    tp2_pct  = ((tp2_price - fill_price) / fill_price) * 100
                    tp3_pct  = ((tp3_price - fill_price) / fill_price) * 100
                    be_note  = ("\\nℹ️ After TP1 hits, stop auto-raises to breakeven."
                                if CFG.breakeven_after_tp1 else
                                "\\nℹ️ TP1 scale-out does not auto-raise stop (CFG flag OFF).")
                    msg_out = (
                        f"OPEN {ticker}: {qty} @ {fill_price:.2f} SAR\\n"
                        f"{'━'*22}\\n"
                        f"📍 Entry      : {fill_price:.2f} SAR "
                        f"(eff. cost {eff_cost:.2f})\\n"
                        f"🛡️ Stop Loss  : {stop_price:.2f} SAR "
                        f"(−{stop_pct:.1f}%)\\n"
                        f"🎯 TP1         : {tp1_price:.2f} SAR "
                        f"(+{tp1_pct:.1f}%)  — exit {tp1_qty} sh ({int(CFG.tp1_scale_out_pct*100)}%)\\n"
                        f"🎯 TP2         : {tp2_price:.2f} SAR "
                        f"(+{tp2_pct:.1f}%)  — exit {tp2_qty} sh ({int(CFG.tp2_scale_out_pct*100)}%)\\n"
                        f"🎯 TP3         : {tp3_price:.2f} SAR "
                        f"(+{tp3_pct:.1f}%)  — close {tp3_qty} sh\\n"
                        f"💰 Risk        : {initial_risk_sar:.2f} SAR "
                        f"({CFG.risk_per_trade_pct*100:.1f}% equity)\\n"
                        f"💸 Commission  : {comm:.2f} SAR"
                        f"{be_note}"
                    )

                await db.execute(
                    """INSERT INTO signal_events
                           (signal_id,position_id,trade_date,reason_code,
                            generated_at,event_source)
                       VALUES(?,?,?,'MANUAL_BUY',?,'MANUAL')""",
                    (sig_id, pos_id, sig_time.date().isoformat(), _now_iso())
                )
                await db.execute(
                    """INSERT INTO transactions
                           (position_id,ticker,transaction_type,signal_time,
                            execution_time,fill_price,quantity,commission_sar,
                            reason_code,equity_snapshot,realized_pnl_sar,
                            modeled_risk_sar)
                       VALUES(?,?,'BUY',?,?,?,?,?,'MANUAL',?,0,?)""",
                    (pos_id, ticker, sig_time.isoformat(), _now_iso(),
                     fill_price, qty, comm, equity, initial_risk_sar)
                )

                await db.execute(
                    """UPDATE setup_log
                       SET entry_taken=1, position_id=?
                       WHERE id = (
                           SELECT id FROM setup_log
                           WHERE ticker=? AND entry_taken=0
                             AND claude_signal='BUY'
                           ORDER BY logged_at DESC LIMIT 1
                       )""",
                    (pos_id, ticker)
                )

                await db.commit()
                return ExecResult(True, msg_out, position_id=pos_id)
            except Exception as exc:
                await db.rollback()
                return ExecResult(False, f"DB error: {exc}")

    async def record_sell(self, ticker: str, fill_price: float,
                          qty: Optional[int], sig_id: str,
                          sig_time: datetime, reason: str = "MANUAL") -> ExecResult:
        if fill_price <= 0:
            return ExecResult(False, "Fill price must be > 0")

        from backend.db.database import assert_db_allowed
        assert_db_allowed()

        async with aiosqlite.connect(self.db) as db:
            db.row_factory = aiosqlite.Row
            try:
                await db.execute("BEGIN IMMEDIATE")

                async with db.execute(
                    "SELECT 1 FROM signal_events WHERE signal_id=?", (sig_id,)
                ) as cur:
                    if await cur.fetchone():
                        await db.rollback()
                        return ExecResult(False, "Command already processed")

                async with db.execute(
                    "SELECT * FROM positions WHERE ticker=? AND position_state!='CLOSED'",
                    (ticker,)
                ) as cur:
                    pos = await cur.fetchone()

                if not pos:
                    await db.rollback()
                    return ExecResult(False, f"No open position found for {ticker}")

                cur_qty  = pos["current_position_size"]
                sell_qty = qty if qty is not None else cur_qty
                if sell_qty > cur_qty:
                    await db.rollback()
                    return ExecResult(False,
                        f"Cannot sell {sell_qty}; only {cur_qty} open")

                new_qty      = cur_qty - sell_qty
                is_full      = new_qty == 0
                new_state    = "CLOSED" if is_full else "PARTIAL"
                closed_at    = sig_time.isoformat() if is_full else None
                comm         = _commission(fill_price, sell_qty)
                tranche_pnl  = (fill_price - pos["avg_cost"]) * sell_qty - comm
                old_equity   = await get_equity(self.db)
                new_equity   = old_equity + tranche_pnl
                new_realized = pos["realized_pnl_sar"] + tranche_pnl
                tx_type      = "SELL" if is_full else "PARTIAL_SELL"

                init_risk_total = pos["initial_risk_sar"] or 0.0
                orig_qty        = pos["original_position_size"] or 1
                tranche_risk    = init_risk_total * (sell_qty / orig_qty) if orig_qty else 0.0
                r_multiple      = round(tranche_pnl / tranche_risk, 2) if tranche_risk > 0 else None
                roi_pct         = round((tranche_pnl / (pos["avg_cost"] * sell_qty)) * 100, 2)

                entry_px = pos["initial_entry_price"]
                atr_ref  = pos["initial_atr"]
                sl_ref   = round(entry_px - (atr_ref * pos["stop_atr_multiple"]), 2)
                modeled_risk_sar  = round(tranche_risk, 2)

                if tranche_pnl < 0:
                    realized_risk_sar = round(abs(tranche_pnl), 2)
                    slippage_sar      = round(realized_risk_sar - modeled_risk_sar, 2)
                else:
                    realized_risk_sar = 0.0
                    slippage_sar      = 0.0

                duration_days: Optional[float] = None
                if is_full:
                    try:
                        opened = datetime.fromisoformat(pos["opened_at"])
                        duration_days = (sig_time - opened).days
                    except Exception:
                        duration_days = None

                tp1_px       = pos["tp1_price"] or 0
                tp2_px       = pos["tp2_price"] or pos["take_profit_price"] or 0
                tp3_px       = pos["tp3_price"] or 0
                tp1_hit_flag = bool(pos["tp1_hit"])
                exit_label   = reason   
                tp_flag      = ""
                sl_flag      = ""

                if fill_price <= sl_ref:
                    exit_label = "SL_HIT"
                    sl_flag    = " 🛡️ SL triggered"
                elif tp3_px > 0 and fill_price >= tp3_px:
                    exit_label = "TP3_HIT"
                    tp_flag    = " 🎯 TP3 hit!"
                elif tp2_px > 0 and fill_price >= tp2_px:
                    exit_label = "TP2_HIT"
                    tp_flag    = " 🎯 TP2 hit!"
                elif tp1_px > 0 and fill_price >= tp1_px:
                    exit_label = "TP1_HIT"
                    tp_flag    = " 🎯 TP1 hit!"

                exit_rsn = exit_label if is_full else pos["exit_reason"]

                be_applied      = False
                new_tp1_hit     = pos["tp1_hit"]
                new_watermark   = pos["highest_close_since_entry"]
                if (not is_full and not tp1_hit_flag and
                        exit_label in ("TP1_HIT", "TP2_HIT", "TP3_HIT") and
                        CFG.breakeven_after_tp1):
                    stop_dist_entry  = atr_ref * pos["stop_atr_multiple"]
                    required_wm      = entry_px + stop_dist_entry
                    new_watermark    = max(new_watermark, required_wm)
                    new_tp1_hit      = 1
                    be_applied       = True

                upd = await db.execute(
                    """UPDATE positions SET
                           current_position_size=?, position_state=?, closed_at=?,
                           exit_reason=?, realized_pnl_sar=?,
                           total_commissions_sar=total_commissions_sar+?,
                           partial_exit_taken=CASE WHEN ? THEN 1
                                              ELSE partial_exit_taken END,
                           tp1_hit=?,
                           highest_close_since_entry=?,
                           version=version+1
                       WHERE id=? AND version=?""",
                    (new_qty, new_state, closed_at, exit_rsn, new_realized,
                     comm, 0 if is_full else 1, new_tp1_hit, new_watermark,
                     pos["id"], pos["version"])
                )
                if upd.rowcount == 0:
                    await db.rollback()
                    return ExecResult(False, "Concurrency conflict — retry")

                await db.execute(
                    """INSERT INTO signal_events
                           (signal_id,position_id,trade_date,reason_code,
                            generated_at,event_source)
                       VALUES(?,?,?,?,?,'MANUAL')""",
                    (sig_id, pos["id"], sig_time.date().isoformat(),
                     exit_label, _now_iso())
                )
                await db.execute(
                    """INSERT INTO transactions
                           (position_id,ticker,transaction_type,signal_time,
                            execution_time,fill_price,quantity,commission_sar,
                            reason_code,equity_snapshot,realized_pnl_sar,
                            r_multiple,duration_days,roi_pct,
                            modeled_risk_sar,realized_risk_sar,slippage_sar)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (pos["id"], ticker, tx_type, sig_time.isoformat(), _now_iso(),
                     fill_price, sell_qty, comm, exit_label, old_equity,
                     tranche_pnl, r_multiple, duration_days, roi_pct,
                     modeled_risk_sar, realized_risk_sar, slippage_sar)
                )
                await db.execute(
                    """INSERT INTO system_state(key,value,updated_at)
                       VALUES('current_equity',?,?)
                       ON CONFLICT(key) DO UPDATE SET
                           value=excluded.value,
                           updated_at=excluded.updated_at""",
                    (str(new_equity), _now_iso())
                )

                if is_full:
                    async with db.execute(
                        """SELECT SUM(r_multiple) AS total_r
                           FROM transactions
                           WHERE position_id=?
                             AND transaction_type IN ('SELL','PARTIAL_SELL')
                             AND r_multiple IS NOT NULL""",
                        (pos["id"],)
                    ) as cur:
                        row = await cur.fetchone()
                    cumulative_r = float(row["total_r"]) if row and row["total_r"] is not None else None
                    if cumulative_r is not None:
                        await db.execute(
                            "UPDATE setup_log SET outcome_r=? WHERE position_id=?",
                            (round(cumulative_r, 2), pos["id"])
                        )

                await db.commit()

                pnl_sign = "+" if tranche_pnl >= 0 else ""
                roi_sign = "+" if roi_pct >= 0 else ""
                r_str    = f"{r_multiple:+.2f}R" if r_multiple is not None else "—"
                dur_str  = f"{int(duration_days)}d" if duration_days is not None else "—"
                slip_str = ""
                if tranche_pnl < 0 and abs(slippage_sar) > 0.01:
                    slip_sign = "+" if slippage_sar >= 0 else ""
                    slip_str  = f"\\n📉 Slippage     : {slip_sign}{slippage_sar:,.2f} SAR (vs {modeled_risk_sar:,.2f} modeled)"

                be_line = ""
                if be_applied:
                    be_line = f"\\n\\n🛡️ <b>Stop auto-raised to breakeven</b> ({entry_px:.2f} SAR)."

                remaining = ""
                if not is_full:
                    remaining_parts = []
                    if tp2_px > 0 and fill_price < tp2_px:
                        remaining_parts.append(f"TP2: {tp2_px:.2f}")
                    if tp3_px > 0 and fill_price < tp3_px:
                        remaining_parts.append(f"TP3: {tp3_px:.2f}")
                    if remaining_parts:
                        remaining = (f"\\n📋 Remaining: {new_qty} shares  |  "
                                     + "  ".join(remaining_parts))

                msg_out = (
                    f"{tx_type} {ticker}: {sell_qty} @ {fill_price:.2f} SAR"
                    f"{tp_flag}{sl_flag}\\n"
                    f"{'━'*22}\\n"
                    f"📍 Entry       : {pos['avg_cost']:.2f} SAR\\n"
                    f"📍 Exit        : {fill_price:.2f} SAR\\n"
                    f"🛡️ Stop Loss   : {sl_ref:.2f} SAR\\n"
                    f"🎯 TP1/TP2/TP3 : {tp1_px:.2f} / {tp2_px:.2f} / {tp3_px:.2f}\\n"
                    f"🏷️ Exit reason : {exit_label}\\n"
                    f"⏱️ Duration    : {dur_str}\\n"
                    f"📈 ROI         : {roi_sign}{roi_pct:.2f}%\\n"
                    f"📊 R-Multiple  : {r_str}\\n"
                    f"💰 Net P&L     : {pnl_sign}{tranche_pnl:,.2f} SAR\\n"
                    f"💸 Commission  : {comm:.2f} SAR"
                    f"{slip_str}\\n"
                    f"💼 Equity      : {new_equity:,.2f} SAR"
                    f"{be_line}"
                    f"{remaining}"
                )
                return ExecResult(True, msg_out, position_id=pos["id"])
            except Exception as exc:
                await db.rollback()
                return ExecResult(False, f"DB error: {exc}")
