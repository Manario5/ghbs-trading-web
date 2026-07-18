from typing import Dict, Any
from .config import CFG

def classify_setup(stock: Dict[str, Any],
                   market_regime: str = "NEUTRAL",
                   sector_breadth: float = 0.5) -> Dict[str, Any]:
    rsi            = stock["rsi"]
    close          = stock["close"]
    open_          = stock.get("open", close)
    vol            = stock["vol_surge"]
    adx            = stock.get("adx14", 0.0)
    macd_hist      = stock.get("macd_hist", 0.0)
    macd_hist_prev = stock.get("macd_hist_prev", macd_hist)

    oversold_rsi   = rsi <= CFG.rsi_oversold
    below_bb_lower = stock["bb_lower"] > 0 and close < stock["bb_lower"]
    oversold       = oversold_rsi or below_bb_lower

    macd_improving = macd_hist > macd_hist_prev
    green_day      = close > open_
    reversal       = macd_improving or green_day

    is_bounce = oversold and reversal

    bounce_reason_parts = []
    if oversold_rsi:   bounce_reason_parts.append("RSI_OVERSOLD")
    if below_bb_lower: bounce_reason_parts.append("CLOSE_BELOW_LOWER_BB")
    if macd_improving: bounce_reason_parts.append("MACD_IMPROVING")
    if green_day:      bounce_reason_parts.append("GREEN_DAY")

    overbought_rsi = rsi >= CFG.rsi_overbought
    above_bb_upper = stock["bb_upper"] > 0 and close > stock["bb_upper"]
    momentum       = overbought_rsi or above_bb_upper

    if market_regime == "BEARISH":
        adx_required     = CFG.adx_min_breakout_bear
        sector_ok        = sector_breadth >= CFG.sector_breadth_bear
        adx_gate_passed  = adx >= adx_required
        is_breakout      = momentum and adx_gate_passed and sector_ok
        breakout_extra   = f"BEAR_ADX{adx_required:.0f}+SECTOR{sector_breadth:.2f}"
    else:
        adx_required     = CFG.adx_min_breakout
        sector_ok        = True
        adx_gate_passed  = adx >= adx_required
        is_breakout      = momentum and adx_gate_passed
        breakout_extra   = f"ADX{adx_required:.0f}"

    breakout_reason_parts = []
    if overbought_rsi:   breakout_reason_parts.append("RSI_OVERBOUGHT")
    if above_bb_upper:   breakout_reason_parts.append("CLOSE_ABOVE_UPPER_BB")
    if adx_gate_passed:  breakout_reason_parts.append(breakout_extra)
    if market_regime == "BEARISH" and sector_ok:
        breakout_reason_parts.append("SECTOR_HEALTHY")

    is_vol = vol >= CFG.vol_surge_threshold

    if is_bounce and is_breakout:
        return dict(
            setup_type="MIXED_SIGNAL",
            mechanical_actionable=1,
            mechanical_reason=f"MIXED: bounce[{'+'.join(bounce_reason_parts)}] AND breakout[{'+'.join(breakout_reason_parts)}]",
        )
    if is_bounce:
        return dict(
            setup_type="BOUNCE_SETUP",
            mechanical_actionable=1,
            mechanical_reason="+".join(bounce_reason_parts) or "BOUNCE",
        )
    if is_breakout:
        return dict(
            setup_type="BREAKOUT_SETUP",
            mechanical_actionable=1,
            mechanical_reason="+".join(breakout_reason_parts) or "BREAKOUT",
        )
    if is_vol:
        return dict(
            setup_type="VOLUME_SURGE",
            mechanical_actionable=1,
            mechanical_reason=f"VOL_SURGE_{vol:.1f}x",
        )

    reason_parts = []
    if oversold and not reversal:
        reason_parts.append("OVERSOLD_NO_REVERSAL")
    if momentum and not adx_gate_passed:
        reason_parts.append(f"BREAKOUT_ADX_WEAK_{adx:.1f}<{adx_required:.0f}")
    if momentum and market_regime == "BEARISH" and not sector_ok:
        reason_parts.append(f"SECTOR_WEAK_{sector_breadth:.2f}")
    reason = "+".join(reason_parts) if reason_parts else "NO_TRIGGER"

    return dict(
        setup_type=None,
        mechanical_actionable=0,
        mechanical_reason=reason,
    )
