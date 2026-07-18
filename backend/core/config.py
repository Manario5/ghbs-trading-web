import math
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SystemConfig:
    initial_equity_sar:    float = 100_000.0
    risk_per_trade_pct:    float = 0.01           # 1% equity risk per trade
    max_notional_pct:      float = 0.15           # 15% cap per name
    max_portfolio_heat:    float = 0.05           # V7.1: 5% total open risk cap
    stop_atr_multiple:     float = 2.5            # Chandelier: watermark − 2.5×ATR(22)
    # ── V7.1: Three-tier take-profit structure (R-multiples) ──
    tp1_r_multiple:        float = 1.0            # TP1 = entry + 1× stop distance
    tp2_r_multiple:        float = 2.0            # TP2 = entry + 2× stop distance
    tp3_r_multiple:        float = 3.0            # TP3 = entry + 3× stop distance
    tp1_scale_out_pct:     float = 0.40           # Exit 40% at TP1
    tp2_scale_out_pct:     float = 0.35           # Exit 35% at TP2
    tp3_scale_out_pct:     float = 0.25           # Exit final 25% at TP3
    breakeven_after_tp1:   bool  = True           # V7.1: configurable — default ON
    tp_rr_multiple:        float = 2.0            # Legacy V7.0 single-TP (kept for back-compat)
    commission_pct:        float = 0.00155        # Derayah 0.155% per side
    rsi_length:            int   = 14
    rsi_oversold:          float = 35.0
    rsi_overbought:        float = 68.0
    vol_surge_threshold:   float = 1.8
    adx_min_breakout:      float = 22.0           # V7.0: standard breakout ADX gate
    adx_min_breakout_bear: float = 28.0           # V7.1: stricter in BEARISH regime
    sector_breadth_bear:   float = 0.50           # V7.1: stock's sector must be ≥50% above 200-SMA
    regime_bullish_threshold: float = 0.60        # V7.1: ≥60% above 200-SMA = BULLISH
    regime_bearish_threshold: float = 0.40        # V7.1: <40% above 200-SMA = BEARISH
    atr_entry_length:      int   = 14
    atr_chandelier_length: int   = 22
    bb_length:             int   = 20
    bb_std:                float = 2.0
    claude_model:          str   = "claude-sonnet-4-6"
    claude_max_tokens:     int   = 500            # V7.1: raised from 450 for Arabic summary
    db_path:               str   = "tasi_ledger.db"
    api_timeout_sec:       float = 30.0
    scout_semaphore:       int   = 5
    # Automated daily scan: Sun–Thu at 14:00 UTC = 17:00 AST
    scan_hour_utc:         int   = 14
    scan_minute_utc:       int   = 0
    scan_days:             tuple = (6, 0, 1, 2, 3)
    # Automated daily backup: 23:00 UTC = 02:00 AST
    backup_hour_utc:       int   = 23
    backup_minute_utc:     int   = 0

CFG = SystemConfig()
