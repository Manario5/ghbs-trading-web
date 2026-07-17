import os
import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.auth.dependencies import get_current_user
from backend.services.market_data_service import MarketDataService
from backend.services.engine_service import get_mock_stock_data
from backend.core.classifier import classify_setup
from backend.core.regime import compute_regime
from backend.core.sizes import SizingEngine
from backend.core.universe import SECTOR_MAP, TIER_MAP
from backend.db.database import get_db

router = APIRouter()

import math

def sanitize_for_json(val):
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
    elif type(val).__name__ in ('float32', 'float64'):
        import numpy as np
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    elif type(val).__name__ in ('int32', 'int64'):
        return int(val)
    elif "NA" in str(type(val)):
        # catch pandas NA
        return None
    elif isinstance(val, dict):
        return {k: sanitize_for_json(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_for_json(v) for v in val]
    return val

@router.post("/analyze/{ticker}")
async def live_preview_analyze(ticker: str, current_user: dict = Depends(get_current_user)):
    enabled = os.getenv("ENABLE_LIVE_ANALYZE_PREVIEW", "false").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=400, detail="Live Analyze Preview is disabled (ENABLE_LIVE_ANALYZE_PREVIEW=false).")
        
    md_enabled = os.getenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"
    if not md_enabled:
        raise HTTPException(status_code=400, detail="Market Data smoke tests are disabled.")
        
    ohlcv_enabled = os.getenv("ENABLE_OHLCV_DIAGNOSTICS", "false").lower() == "true"
    if not ohlcv_enabled:
        raise HTTPException(status_code=400, detail="OHLCV Diagnostics are disabled.")

    lookback = int(os.getenv("LIVE_ANALYZE_LOOKBACK_DAYS", "180"))
    
    md_svc = MarketDataService()
    
    provider_status = await md_svc.get_provider_status()
    if not provider_status.get("configured"):
        raise HTTPException(status_code=400, detail=provider_status.get("safe_message", "Market data provider not configured."))

    sym_map = md_svc.get_symbol_map()
    ticker_obj = next((m for m in sym_map if m["internal_ticker"] == ticker), None)
    
    if not ticker_obj:
        raise HTTPException(status_code=400, detail=f"Ticker {ticker} not found in symbol map.")
        
    yfinance_sym = ticker_obj["yfinance_symbol"]
    
    ohlcv_res = await md_svc.test_historical_ohlcv(yfinance_sym, lookback)
    
    if "error" in ohlcv_res:
        raise HTTPException(status_code=400, detail=ohlcv_res["error"])
        
    bars_returned = ohlcv_res.get("bars_returned", 0)
    min_required = ohlcv_res.get("min_required_bars", 120)
    
    warnings = []
    if bars_returned < min_required:
        warnings.append(f"Insufficient bars: {bars_returned} / {min_required}")
        
    missing_cols = []
    if not ohlcv_res.get("has_open"): missing_cols.append("Open")
    if not ohlcv_res.get("has_high"): missing_cols.append("High")
    if not ohlcv_res.get("has_low"): missing_cols.append("Low")
    if not ohlcv_res.get("has_close"): missing_cols.append("Close")
    if not ohlcv_res.get("has_volume"): missing_cols.append("Volume")
    
    if missing_cols:
        warnings.append(f"Missing columns: {','.join(missing_cols)}")
        
    data_quality = "OK" if not warnings else "WARNINGS"
    
    # We create a mock stock dict for strategy functions, but override with actual OHLCV latest close
    stock = get_mock_stock_data(ticker)
    
    latest_close = ohlcv_res.get("latest_close", 0)
    latest_volume = ohlcv_res.get("latest_volume", 0)
    
    if latest_close:
        stock["close"] = latest_close
    if latest_volume:
        stock["volume"] = latest_volume
        
    regime_data = compute_regime([stock])
    market_regime = regime_data.get("regime", "UNKNOWN")
    
    setup_result = classify_setup(stock, market_regime=market_regime, sector_breadth=0.5)
    setup_type = setup_result.get("setup_type", "NONE")
    
    signal = "BUY" if setup_result.get("mechanical_actionable") else "HOLD"
    
    equity = 100000.0  # static equity for preview
    sizing_preview = None
    stop_preview = None
    
    if signal == "BUY" and latest_close > 0:
        atr = stock.get("atr22", 2.2)
        prop = SizingEngine.propose(equity, latest_close, atr, risk_pct=0.01)
        if not prop.reject_reason:
            sizing_preview = prop.shares
            stop_preview = prop.stop_price
            
    diagnostic_summary = setup_result.get("mechanical_reason", "NO_TRIGGER")
    
    if signal == "BUY":
        # Handle "MIXED: bounce[RSI_OVERSOLD] AND breakout[RSI_OVERBOUGHT]" parsing safely
        signal_reasons = [r for r in diagnostic_summary.replace(" AND ", "+").replace("MIXED: bounce[", "").replace("] breakout[", "+").replace("]", "").split("+") if r]
        blocking_reasons = []
    else:
        signal_reasons = []
        blocking_reasons = diagnostic_summary.split("+")
        
    indicator_snapshot = {
        "RSI": stock.get("rsi"),
        "ADX": stock.get("adx14"),
        "volume_ratio": stock.get("vol_surge"),
        "close_vs_bb_upper": stock.get("close", 0) - stock.get("bb_upper", 0) if stock.get("bb_upper") else None,
        "close_vs_bb_lower": stock.get("close", 0) - stock.get("bb_lower", 0) if stock.get("bb_lower") else None,
        "close_vs_ma20": stock.get("close", 0) - stock.get("sma20", 0) if stock.get("sma20") else None,
        "close_vs_ma50": stock.get("close", 0) - stock.get("sma50", 0) if stock.get("sma50") else None,
        "atr": stock.get("atr22")
    }

    from backend.core.config import CFG
    thresholds_snapshot = {
        "adx_threshold_used": CFG.adx_min_breakout_bear if market_regime == "BEARISH" else CFG.adx_min_breakout,
        "vol_surge_threshold_used": CFG.vol_surge_threshold,
        "rsi_oversold_threshold_used": CFG.rsi_oversold,
        "rsi_overbought_threshold_used": CFG.rsi_overbought,
        "min_required_bars": min_required
    }

    message = "Live Preview Generated successfully." if not warnings else "Live Preview Generated with warnings."
        
    payload = {
        "ticker": ticker,
        "provider": ohlcv_res.get("provider", "unknown"),
        "provider_ticker": ohlcv_res.get("provider_ticker", yfinance_sym),
        "bars_returned": bars_returned,
        "date_range": f"{ohlcv_res.get('start_date', '')} to {ohlcv_res.get('end_date', '')}",
        "latest_close": latest_close,
        "latest_volume": latest_volume,
        "regime": market_regime,
        "setup_type": setup_type,
        "signal": signal,
        "sizing_preview": sizing_preview,
        "stop_preview": stop_preview,
        "diagnostic_summary": diagnostic_summary,
        "signal_reasons": signal_reasons,
        "blocking_reasons": blocking_reasons,
        "indicator_snapshot": indicator_snapshot,
        "thresholds_snapshot": thresholds_snapshot,
        "warnings": warnings,
        "data_quality": data_quality,
        "is_mocked": ohlcv_res.get("is_mocked", True),
        "sandbox_only": True,
        "execution_allowed": False,
        "message": message
    }
    
    sanitized_payload = sanitize_for_json(payload)
    
    # If any computed value was NaN, add a warning
    has_nans = False
    for k, v in payload.items():
        if v is not None and sanitized_payload[k] is None:
            has_nans = True
            
    if has_nans:
        sanitized_payload["warnings"].append("Some preview fields were unavailable because one or more calculated values were NaN.")
        
    # Save audit log
    async for db in get_db():
        try:
            await db.execute("""
                INSERT INTO live_preview_runs 
                (created_at, preview_type, provider, ticker_count, requested_ticker, scanned_count, eligible_count, blocked_count, data_failures, payload_json, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "analyze",
                sanitized_payload.get("provider", md_svc.provider),
                1,
                ticker,
                1,
                1 if signal == "BUY" else 0,
                0 if signal == "BUY" else 1,
                1 if data_quality == "FAIL" else 0,
                json.dumps(sanitized_payload),
                "Live Analyze Preview Run"
            ))
            await db.commit()
        except Exception as e:
            print(f"Failed to log live preview run: {e}")
        break
        
    return sanitized_payload

@router.post("/scout")
async def live_preview_scout(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        body = await request.json()
    except Exception:
        body = {}
    filters = body.get("filters", {})
    
    enabled = os.getenv("ENABLE_LIVE_SCOUT_PREVIEW", "false").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=400, detail="Live Scout Preview is disabled (ENABLE_LIVE_SCOUT_PREVIEW=false).")

    md_enabled = os.getenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"
    if not md_enabled:
        raise HTTPException(status_code=400, detail="Market Data smoke tests are disabled.")

    ohlcv_enabled = os.getenv("ENABLE_OHLCV_DIAGNOSTICS", "false").lower() == "true"
    if not ohlcv_enabled:
        raise HTTPException(status_code=400, detail="OHLCV Diagnostics are disabled.")

    lookback = int(os.getenv("LIVE_SCOUT_LOOKBACK_DAYS", "180"))
    limit = int(os.getenv("LIVE_SCOUT_LIMIT", "10"))

    md_svc = MarketDataService()

    provider_status = await md_svc.get_provider_status()
    if not provider_status.get("configured"):
        raise HTTPException(status_code=400, detail=provider_status.get("safe_message", "Market data provider not configured."))

    sym_map = md_svc.get_symbol_map()
    universe_size = len(sym_map)
    universe = sym_map[:limit]

    results = []
    eligible_count = 0
    blocked_count = 0
    data_quality_failures = 0

    for item in universe:
        ticker = item["internal_ticker"]
        yfinance_sym = item["yfinance_symbol"]
        
        ohlcv_res = await md_svc.test_historical_ohlcv(yfinance_sym, lookback)
        
        warnings = []
        if "error" in ohlcv_res:
            data_quality_failures += 1
            results.append({
                "ticker": ticker,
                "provider_ticker": yfinance_sym,
                "tier": TIER_MAP.get(ticker, "Unknown"),
                "sector": SECTOR_MAP.get(ticker, "Unknown"),
                "bars_returned": 0,
                "latest_close": None,
                "latest_volume": None,
                "data_quality": "FAIL",
                "regime": None,
                "setup_type": None,
                "signal": None,
                "warnings": [ohlcv_res["error"]],
                "is_mocked": True,
                "execution_allowed": False,
                "sandbox_only": True
            })
            continue
            
        bars_returned = ohlcv_res.get("bars_returned", 0)
        min_required = ohlcv_res.get("min_required_bars", 120)
        
        if bars_returned < min_required:
            warnings.append(f"Insufficient bars: {bars_returned} / {min_required}")
            
        missing_cols = []
        if not ohlcv_res.get("has_open"): missing_cols.append("Open")
        if not ohlcv_res.get("has_high"): missing_cols.append("High")
        if not ohlcv_res.get("has_low"): missing_cols.append("Low")
        if not ohlcv_res.get("has_close"): missing_cols.append("Close")
        if not ohlcv_res.get("has_volume"): missing_cols.append("Volume")
        
        if missing_cols:
            warnings.append(f"Missing columns: {','.join(missing_cols)}")
            
        data_quality = "OK" if not warnings else "WARNINGS"
        if warnings:
            data_quality_failures += 1
        
        # We create a mock stock dict for strategy functions, but override with actual OHLCV latest close
        stock = get_mock_stock_data(ticker)
        
        latest_close = ohlcv_res.get("latest_close", 0)
        latest_volume = ohlcv_res.get("latest_volume", 0)
        
        if latest_close is not None:
            stock["close"] = latest_close
        if latest_volume is not None:
            stock["volume"] = latest_volume
            
        regime_data = compute_regime([stock])
        market_regime = regime_data.get("regime", "UNKNOWN")
        
        setup_result = classify_setup(stock, market_regime=market_regime, sector_breadth=0.5)
        setup_type = setup_result.get("setup_type", "NONE")
        
        signal = "BUY" if setup_result.get("mechanical_actionable") else "HOLD"
        
        diagnostic_summary = setup_result.get("mechanical_reason", "NO_TRIGGER")
        
        if signal == "BUY":
            signal_reasons = [r for r in diagnostic_summary.replace(" AND ", "+").replace("MIXED: bounce[", "").replace("] breakout[", "+").replace("]", "").split("+") if r]
            blocking_reasons = []
        else:
            signal_reasons = []
            blocking_reasons = diagnostic_summary.split("+")
            
        indicator_snapshot = {
            "RSI": stock.get("rsi"),
            "ADX": stock.get("adx14"),
            "volume_ratio": stock.get("vol_surge"),
            "close_vs_bb_upper": stock.get("close", 0) - stock.get("bb_upper", 0) if stock.get("bb_upper") else None,
            "close_vs_bb_lower": stock.get("close", 0) - stock.get("bb_lower", 0) if stock.get("bb_lower") else None,
            "close_vs_ma20": stock.get("close", 0) - stock.get("sma20", 0) if stock.get("sma20") else None,
            "close_vs_ma50": stock.get("close", 0) - stock.get("sma50", 0) if stock.get("sma50") else None,
            "atr": stock.get("atr22")
        }

        from backend.core.config import CFG
        thresholds_snapshot = {
            "adx_threshold_used": CFG.adx_min_breakout_bear if market_regime == "BEARISH" else CFG.adx_min_breakout,
            "vol_surge_threshold_used": CFG.vol_surge_threshold,
            "rsi_oversold_threshold_used": CFG.rsi_oversold,
            "rsi_overbought_threshold_used": CFG.rsi_overbought,
            "min_required_bars": min_required
        }

        if signal == "BUY":
            eligible_count += 1
        else:
            blocked_count += 1
            
        tier = TIER_MAP.get(ticker, "Unknown")
        score_components = {
            "tier_priority": 10 if tier == "TIER_1" else 5 if tier == "TIER_2" else 0,
            "signal_buy": 20 if signal == "BUY" else 0,
            "quality_ok": 10 if data_quality == "OK" else -10,
            "setup_breakout": 10 if "BREAKOUT" in setup_type else 5 if setup_type != "NONE" else 0,
            "adx_strength": min(20, int(stock.get("adx14", 0) / 2)) if stock.get("adx14") else 0,
            "vol_strength": min(10, int(stock.get("vol_surge", 0) * 2)) if stock.get("vol_surge") else 0,
            "no_blocking_reasons": 15 if not blocking_reasons and signal == "BUY" else 0
        }
        candidate_score = sum(score_components.values())
        review_bucket = "High Priority" if candidate_score >= 60 else "Review" if candidate_score >= 30 else "Discard"

        res_payload = {
            "ticker": ticker,
            "provider_ticker": yfinance_sym,
            "tier": tier,
            "sector": SECTOR_MAP.get(ticker, "Unknown"),
            "bars_returned": bars_returned,
            "latest_close": latest_close,
            "latest_volume": latest_volume,
            "data_quality": data_quality,
            "regime": market_regime,
            "setup_type": setup_type,
            "signal": signal,
            "diagnostic_summary": diagnostic_summary,
            "signal_reasons": signal_reasons,
            "blocking_reasons": blocking_reasons,
            "indicator_snapshot": indicator_snapshot,
            "thresholds_snapshot": thresholds_snapshot,
            "candidate_score": candidate_score,
            "score_components": score_components,
            "review_bucket": review_bucket,
            "warnings": warnings,
            "is_mocked": ohlcv_res.get("is_mocked", True),
            "execution_allowed": False,
            "sandbox_only": True
        }
        
        sanitized_res = sanitize_for_json(res_payload)
        
        # If any computed value was NaN, add a warning
        has_nans = False
        for k, v in res_payload.items():
            if v is not None and sanitized_res[k] is None:
                has_nans = True
                
        if has_nans:
            sanitized_res["warnings"].append("Some preview fields were unavailable because one or more calculated values were NaN.")
            
        results.append(sanitized_res)
        
    # Sort and rank results
    results = sorted(results, key=lambda x: x.get("candidate_score", 0), reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    final_payload = {
        "provider": md_svc.provider,
        "universe_size": universe_size,
        "scanned_count": len(universe),
        "eligible_count": eligible_count,
        "blocked_count": blocked_count,
        "data_quality_failures": data_quality_failures,
        "filters_applied": filters,
        "results": results,
    }
    
    sanitized_final = sanitize_for_json(final_payload)
    
    # Save audit log
    async for db in get_db():
        try:
            await db.execute("""
                INSERT INTO live_preview_runs 
                (created_at, preview_type, provider, ticker_count, requested_ticker, scanned_count, eligible_count, blocked_count, data_failures, payload_json, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "scout",
                md_svc.provider,
                universe_size,
                None,
                len(universe),
                eligible_count,
                blocked_count,
                data_quality_failures,
                json.dumps(sanitized_final),
                "Live Scout Preview Run"
            ))
            await db.commit()
        except Exception as e:
            print(f"Failed to log live scout preview run: {e}")
        break

    return sanitized_final

@router.get("/runs")
async def get_live_preview_runs(current_user: dict = Depends(get_current_user)):
    async for db in get_db():
        cursor = await db.execute("SELECT id, created_at, preview_type, provider, ticker_count, requested_ticker, scanned_count, eligible_count, blocked_count, data_failures, notes FROM live_preview_runs ORDER BY id DESC LIMIT 100")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

@router.get("/runs/{run_id}")
async def get_live_preview_run(run_id: int, current_user: dict = Depends(get_current_user)):
    async for db in get_db():
        cursor = await db.execute("SELECT * FROM live_preview_runs WHERE id = ?", (run_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Live preview run not found")
        data = dict(row)
        
        raw_payload = {}
        if data.get("payload_json"):
            try:
                raw_payload = json.loads(data["payload_json"])
            except Exception:
                pass
            
        if "payload_json" in data:
            del data["payload_json"]
            
        status_val = "success"
        if data.get("data_failures", 0) > 0 and data.get("eligible_count", 0) == 0:
            status_val = "failed"
        elif data.get("data_failures", 0) > 0 and data.get("eligible_count", 0) > 0:
            status_val = "partial"
            
        candidates = []
        regime_val = "NEUTRAL"
        warnings = []
        filters_applied = {}
        signals = 0
        
        if isinstance(raw_payload, dict):
            filters_applied = raw_payload.get("filters_applied", {})
            results = raw_payload.get("results", [])
            warnings = raw_payload.get("warnings", [])
            
            if data["preview_type"] == "analyze":
                if "ticker" in raw_payload:
                    candidates.append({
                        "ticker": raw_payload.get("ticker"),
                        "tier": raw_payload.get("tier", "Unknown"),
                        "segment": raw_payload.get("sector", "Unknown"),
                        "setup_type": raw_payload.get("setup_type"),
                        "claude_signal": None,
                        "confidence": None,
                        "mechanical_reason": raw_payload.get("diagnostic_summary"),
                        "actionable": raw_payload.get("signal") == "BUY",
                        "blocked": raw_payload.get("signal") != "BUY",
                        "entry_taken": False,
                        "outcome_r": None,
                        "signal": raw_payload.get("signal")
                    })
                    regime_val = raw_payload.get("regime", "NEUTRAL")
                    if raw_payload.get("signal") == "BUY":
                        signals += 1
                    if "warnings" in raw_payload and raw_payload["warnings"]:
                        warnings = raw_payload["warnings"]
            else:
                for r in results:
                    if r.get("signal") == "BUY":
                        signals += 1
                    candidates.append({
                        "ticker": r.get("ticker"),
                        "tier": r.get("tier", "Unknown"),
                        "segment": r.get("sector", "Unknown"),
                        "setup_type": r.get("setup_type"),
                        "claude_signal": None,
                        "confidence": None,
                        "mechanical_reason": r.get("diagnostic_summary"),
                        "actionable": r.get("signal") == "BUY",
                        "blocked": r.get("signal") != "BUY",
                        "entry_taken": False,
                        "outcome_r": None,
                        "signal": r.get("signal")
                    })
                    if r.get("regime"):
                        regime_val = r.get("regime", "NEUTRAL")
                
        return {
            "id": data["id"],
            "created_at": data["created_at"],
            "event_type": data["preview_type"],
            "status": status_val,
            "summary": {
                "fetched": data.get("scanned_count", 0),
                "failed": data.get("data_failures", 0),
                "actionable": data.get("eligible_count", 0),
                "blocked": data.get("blocked_count", 0),
                "claude_calls": 0,
                "signals": signals,
                "regime": regime_val
            },
            "filters_applied": filters_applied,
            "candidates": candidates,
            "warnings": warnings,
            "raw_payload": raw_payload
        }

@router.delete("/runs/{run_id}")
async def delete_live_preview_run(run_id: int, current_user: dict = Depends(get_current_user)):
    async for db in get_db():
        await db.execute("DELETE FROM live_preview_runs WHERE id = ?", (run_id,))
        await db.commit()
        return {"status": "ok"}