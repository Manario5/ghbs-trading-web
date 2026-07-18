import math
from dataclasses import dataclass
from typing import Optional
from .config import CFG

@dataclass(slots=True)
class SizeProposal:
    shares: int
    notional: float
    stop_price: float
    tp1_price: float
    tp2_price: float
    tp3_price: float
    tp1_shares: int
    tp2_shares: int
    tp3_shares: int
    risk_amount: float
    reject_reason: Optional[str] = None
    tp_price: float = 0.0

class SizingEngine:
    @staticmethod
    def propose(equity: float, price: float, atr: float,
                risk_pct: Optional[float] = None) -> SizeProposal:
        rp = risk_pct if risk_pct is not None else CFG.risk_per_trade_pct
        if price <= 0 or atr <= 0:
            return SizeProposal(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "Invalid price or ATR")

        stop_dist   = atr * CFG.stop_atr_multiple
        tp1_dist    = stop_dist * CFG.tp1_r_multiple
        tp2_dist    = stop_dist * CFG.tp2_r_multiple
        tp3_dist    = stop_dist * CFG.tp3_r_multiple
        risk_budget = equity * rp
        shares      = math.floor(risk_budget / stop_dist)

        if shares < 1:
            return SizeProposal(
                0, 0,
                price - stop_dist,
                price + tp1_dist, price + tp2_dist, price + tp3_dist,
                0, 0, 0, 0,
                "Insufficient risk capital",
            )

        notional = shares * price
        cap      = equity * CFG.max_notional_pct
        if notional > cap:
            shares   = math.floor(cap / price)
            notional = shares * price
            if shares < 1:
                return SizeProposal(
                    0, 0,
                    price - stop_dist,
                    price + tp1_dist, price + tp2_dist, price + tp3_dist,
                    0, 0, 0, 0,
                    "Notional cap → 0 shares",
                )

        tp1_qty = math.floor(shares * CFG.tp1_scale_out_pct)
        tp2_qty = math.floor(shares * CFG.tp2_scale_out_pct)
        tp3_qty = shares - tp1_qty - tp2_qty

        return SizeProposal(
            shares=shares,
            notional=notional,
            stop_price=price - stop_dist,
            tp1_price=price + tp1_dist,
            tp2_price=price + tp2_dist,
            tp3_price=price + tp3_dist,
            tp1_shares=tp1_qty,
            tp2_shares=tp2_qty,
            tp3_shares=tp3_qty,
            risk_amount=shares * stop_dist,
            tp_price=price + (stop_dist * CFG.tp_rr_multiple),
        )
