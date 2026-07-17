from typing import List, Dict, Any
from .config import CFG
from .universe import SECTOR_MAP, TIER_MAP

def compute_regime(all_stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid = [s for s in all_stocks if s is not None]
    if not valid:
        return dict(regime="NEUTRAL", market_breadth=0.5, above_count=0,
                    total_count=0, sector_breadth={}, tier_breadth={})

    above_count = sum(1 for s in valid if s.get("above_sma200"))
    total_count = len(valid)
    breadth     = above_count / total_count if total_count else 0.5

    if breadth >= CFG.regime_bullish_threshold:
        regime = "BULLISH"
    elif breadth < CFG.regime_bearish_threshold:
        regime = "BEARISH"
    else:
        regime = "NEUTRAL"

    sector_stats: Dict[str, List[int]] = {}
    for s in valid:
        sec = SECTOR_MAP.get(s["ticker"], "Other")
        sector_stats.setdefault(sec, []).append(1 if s.get("above_sma200") else 0)

    sector_breadth = {
        sec: sum(flags) / len(flags)
        for sec, flags in sector_stats.items()
        if flags
    }

    tier_stats: Dict[str, List[int]] = {}
    for s in valid:
        tier = TIER_MAP.get(s["ticker"], "UNKNOWN")
        tier_stats.setdefault(tier, []).append(1 if s.get("above_sma200") else 0)

    tier_breadth = {
        tier: sum(flags) / len(flags)
        for tier, flags in tier_stats.items()
        if flags
    }

    return dict(
        regime=regime,
        market_breadth=round(breadth, 3),
        above_count=above_count,
        total_count=total_count,
        sector_breadth=sector_breadth,
        tier_breadth=tier_breadth,
    )

def get_sector_breadth(ticker: str, regime_data: Dict[str, Any]) -> float:
    sector = SECTOR_MAP.get(ticker, "Other")
    sector_breadth_map = regime_data.get("sector_breadth", {})
    return sector_breadth_map.get(sector, regime_data.get("market_breadth", 0.5))
