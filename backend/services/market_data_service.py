import os
import httpx
import logging
from datetime import datetime, timezone
import random

logger = logging.getLogger(__name__)

_LAST_COVERAGE_SCAN_RESULT = None

class MarketDataService:
    def __init__(self):
        self.provider = os.getenv("MARKET_DATA_PROVIDER", "mock").lower()
        self.sample_ticker = os.getenv("MARKET_DATA_SAMPLE_TICKER", "2222.SR")
        
    async def get_provider_coverage_last(self):
        global _LAST_COVERAGE_SCAN_RESULT
        if _LAST_COVERAGE_SCAN_RESULT is None:
            return {"error": "No coverage scan has been run yet."}
        return {"success": True, "data": _LAST_COVERAGE_SCAN_RESULT}

    async def run_provider_coverage_scan(self, limit: int = 80):
        global _LAST_COVERAGE_SCAN_RESULT
        
        md_enabled = os.getenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"
        if not md_enabled:
            return {"error": "Market Data smoke tests are disabled."}
            
        ohlcv_enabled = os.getenv("ENABLE_OHLCV_DIAGNOSTICS", "false").lower() == "true"
        if not ohlcv_enabled:
            return {"error": "OHLCV Diagnostics are disabled."}
            
        cov_enabled = os.getenv("ENABLE_PROVIDER_COVERAGE_SCAN", "false").lower() == "true"
        if not cov_enabled:
            return {"error": "Provider Coverage Scan is disabled (ENABLE_PROVIDER_COVERAGE_SCAN=false)."}
            
        universe = self.get_symbol_map()[:limit]
        from backend.core.universe import TIER_MAP, SECTOR_MAP
        lookback_days = int(os.getenv("PROVIDER_COVERAGE_LOOKBACK_DAYS", "180"))
        
        results = []
        
        for item in universe:
            internal_ticker = item["internal_ticker"]
            yfinance_sym = item["yfinance_symbol"]
            
            quote_res = await self.test_sample_quote(yfinance_sym)
            ohlcv_res = await self.test_historical_ohlcv(yfinance_sym, lookback_days)
            
            quote_status = "success" if "error" not in quote_res else "failed"
            quote_price = quote_res.get("price") if quote_status == "success" else None
            
            ohlcv_status = "success" if "error" not in ohlcv_res else "failed"
            bars_returned = ohlcv_res.get("bars_returned") if ohlcv_status == "success" else None
            min_required = ohlcv_res.get("min_required_bars") if ohlcv_status == "success" else None
            
            if ohlcv_status == "success" and bars_returned is not None and min_required is not None:
                if bars_returned < min_required:
                    ohlcv_status = "insufficient"
            
            missing_cols = []
            if ohlcv_status in ["success", "insufficient"]:
                if not ohlcv_res.get("has_open"): missing_cols.append("Open")
                if not ohlcv_res.get("has_high"): missing_cols.append("High")
                if not ohlcv_res.get("has_low"): missing_cols.append("Low")
                if not ohlcv_res.get("has_close"): missing_cols.append("Close")
                if not ohlcv_res.get("has_volume"): missing_cols.append("Volume")
                
            safe_message = "Quote & OHLCV OK"
            if quote_status != "success":
                safe_message = quote_res.get("error", "Quote Failed")
            elif ohlcv_status == "failed":
                safe_message = ohlcv_res.get("error", "OHLCV Failed")
            elif ohlcv_status == "insufficient":
                safe_message = f"Insufficient Bars: {bars_returned}/{min_required}"
            elif len(missing_cols) > 0:
                safe_message = f"Missing: {','.join(missing_cols)}"

            res_obj = {
                "internal_ticker": internal_ticker,
                "provider_ticker": quote_res.get("provider_ticker") or ohlcv_res.get("provider_ticker") or yfinance_sym,
                "provider": self.provider,
                "tier": item["tier"],
                "sector": item["sector"],
                "quote_status": quote_status,
                "quote_price": quote_price,
                "ohlcv_status": ohlcv_status,
                "bars_returned": bars_returned,
                "min_required_bars": min_required,
                "latest_close": ohlcv_res.get("latest_close") if ohlcv_status in ["success", "insufficient"] else None,
                "latest_volume": ohlcv_res.get("latest_volume") if ohlcv_status in ["success", "insufficient"] else None,
                "missing_columns": missing_cols,
                "is_mocked": quote_res.get("is_mocked", True),
                "safe_message": safe_message
            }
            results.append(res_obj)
            
        summary = {
            "total_tested": len(results),
            "quote_success": sum(1 for r in results if r["quote_status"] == "success"),
            "ohlcv_success": sum(1 for r in results if r["ohlcv_status"] == "success"),
            "insufficient_bars": sum(1 for r in results if r["ohlcv_status"] == "insufficient"),
            "failures": sum(1 for r in results if r["quote_status"] == "failed" or r["ohlcv_status"] == "failed"),
            "is_mocked": self.provider == "mock",
            "provider": self.provider,
            "lookback_days": lookback_days
        }
            
        payload = {
            "summary": summary,
            "results": results
        }
        _LAST_COVERAGE_SCAN_RESULT = payload
        return {"success": True, "data": payload}

    async def get_provider_status(self):
        enabled = os.getenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"
        td_key = os.getenv("TWELVEDATA_API_KEY", "")
        
        status = {
            "provider_name": self.provider,
            "configured": True,
            "enabled": enabled,
            "sample_ticker": self.sample_ticker,
            "safe_message": f"Provider set to {self.provider}."
        }
        
        if self.provider == "twelvedata" and not td_key:
            status["configured"] = False
            status["safe_message"] = "TwelveData is selected but TWELVEDATA_API_KEY is missing."
        elif self.provider == "yfinance":
            try:
                import yfinance
            except ImportError:
                status["configured"] = False
                status["safe_message"] = "yfinance is selected but not installed."

        return status

    def get_symbol_map(self):
        from backend.core.universe import WATCHLIST, TIER_MAP, SECTOR_MAP
        
        results = []
        for internal in WATCHLIST:
            yfinance_sym = f"{internal}.SR"
            twelvedata_sym = f"{internal}:Tadawul"
            
            results.append({
                "internal_ticker": internal,
                "yfinance_symbol": yfinance_sym,
                "twelvedata_symbol": twelvedata_sym,
                "sector": SECTOR_MAP.get(internal, "Unknown"),
                "tier": TIER_MAP.get(internal, "Unknown"),
                "provider_status": "Ready"
            })
        return results

    async def test_universe_sample(self, limit: int = 5):
        enabled = os.getenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"
        if not enabled:
            return {"error": "Smoke tests are disabled (ENABLE_MARKET_DATA_SMOKE_TESTS=false)."}

        universe = self.get_symbol_map()[:limit]
        results = []
        
        for item in universe:
            # We use the yfinance format as our standard 'input_ticker' 
            # because our test_sample_quote method already normalizes .SR correctly
            quote_res = await self.test_sample_quote(item["yfinance_symbol"])
            
            if "error" in quote_res:
                results.append({
                    "ticker": item["internal_ticker"],
                    "provider_ticker": "N/A",
                    "provider": self.provider,
                    "status": "failed",
                    "price": None,
                    "currency": None,
                    "is_mocked": None,
                    "safe_message": quote_res["error"]
                })
            else:
                results.append({
                    "ticker": item["internal_ticker"],
                    "provider_ticker": quote_res.get("provider_ticker"),
                    "provider": quote_res.get("provider"),
                    "status": "success",
                    "price": quote_res.get("price"),
                    "currency": quote_res.get("currency"),
                    "is_mocked": quote_res.get("is_mocked"),
                    "safe_message": quote_res.get("message")
                })
                
        return {"success": True, "results": results}

    async def test_historical_ohlcv(self, ticker: str, lookback_days: int):
        if not ticker:
            ticker = self.sample_ticker

        enabled = os.getenv("ENABLE_OHLCV_DIAGNOSTICS", "false").lower() == "true"
        if not enabled:
            return {"error": "OHLCV Diagnostics are disabled (ENABLE_OHLCV_DIAGNOSTICS=false)."}
            
        md_enabled = os.getenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"
        if not md_enabled:
            return {"error": "Market Data smoke tests are disabled."}

        status = await self.get_provider_status()
        if not status["configured"]:
            return {"error": status["safe_message"]}

        min_required = int(os.getenv("OHLCV_MIN_REQUIRED_BARS", "120"))
        input_ticker = ticker
        
        if self.provider == "mock":
            bars_returned = lookback_days if lookback_days > 0 else min_required
            return {
                "input_ticker": input_ticker,
                "provider_ticker": input_ticker,
                "provider": "mock",
                "start_date": "2023-01-01",
                "end_date": "2023-06-01",
                "bars_returned": bars_returned,
                "min_required_bars": min_required,
                "has_open": True,
                "has_high": True,
                "has_low": True,
                "has_close": True,
                "has_volume": True,
                "latest_close": round(random.uniform(50.0, 150.0), 2),
                "latest_volume": int(random.uniform(10000, 500000)),
                "status": "success",
                "safe_message": "Mock OHLCV generated successfully.",
                "is_mocked": True
            }
            
        elif self.provider == "twelvedata":
            provider_ticker = input_ticker
            if provider_ticker.endswith(".SR"):
                provider_ticker = provider_ticker.replace(".SR", "") + ":Tadawul"
                
            api_key = os.getenv("TWELVEDATA_API_KEY", "")
            outputsize = min(lookback_days, 5000)
            url = f"https://api.twelvedata.com/time_series?symbol={provider_ticker}&interval=1day&outputsize={outputsize}&apikey={api_key}"
            
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, timeout=10.0)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    if "values" in data and len(data["values"]) > 0:
                        values = data["values"]
                        latest = values[0]
                        return {
                            "input_ticker": input_ticker,
                            "provider_ticker": provider_ticker,
                            "provider": "twelvedata",
                            "start_date": values[-1].get("datetime", ""),
                            "end_date": latest.get("datetime", ""),
                            "bars_returned": len(values),
                            "min_required_bars": min_required,
                            "has_open": "open" in latest,
                            "has_high": "high" in latest,
                            "has_low": "low" in latest,
                            "has_close": "close" in latest,
                            "has_volume": "volume" in latest,
                            "latest_close": float(latest.get("close", 0)),
                            "latest_volume": float(latest.get("volume", 0)),
                            "status": "success",
                            "safe_message": "Live OHLCV retrieved successfully.",
                            "is_mocked": False
                        }
                    else:
                        safe_error = data.get("message", "Unknown API format.")
                        if "403" in str(safe_error) or "plan" in str(safe_error).lower() or "access" in str(safe_error).lower() or "permission" in str(safe_error).lower():
                            return {"error": "TwelveData may require Tadawul access on your plan."}
                        return {"error": "Provider rejected the symbol or access is not available for this plan."}
            except Exception as e:
                logger.error(f"Error fetching OHLCV from TwelveData: {str(e)}")
                return {"error": "Provider rejected the symbol or access is not available for this plan."}

        elif self.provider == "yfinance":
            provider_ticker = input_ticker
            try:
                import yfinance as yf
                import asyncio
                import pandas as pd
                from datetime import timedelta
                
                def fetch_yf_ohlcv(t, days):
                    ticker_obj = yf.Ticker(t)
                    hist = ticker_obj.history(period=f"{days}d")
                    if hist.empty:
                        raise ValueError("No historical data found in yfinance.")
                    return hist

                hist = await asyncio.to_thread(fetch_yf_ohlcv, provider_ticker, lookback_days)
                if "Close" in hist.columns:
                    hist = hist.dropna(subset=["Close"])
                if hist.empty:
                    return {"error": "All historical data contained NaN for Close."}
                latest = hist.iloc[-1]
                
                start_dt = str(hist.index[0].date()) if not hist.empty else ""
                end_dt = str(hist.index[-1].date()) if not hist.empty else ""
                return {
                    "input_ticker": input_ticker,
                    "provider_ticker": provider_ticker,
                    "provider": "yfinance",
                    "start_date": start_dt,
                    "end_date": end_dt,
                    "bars_returned": len(hist),
                    "min_required_bars": min_required,
                    "has_open": "Open" in hist.columns,
                    "has_high": "High" in hist.columns,
                    "has_low": "Low" in hist.columns,
                    "has_close": "Close" in hist.columns,
                    "has_volume": "Volume" in hist.columns,
                    "latest_close": float(latest.get("Close", 0)),
                    "latest_volume": float(latest.get("Volume", 0)),
                    "status": "success",
                    "safe_message": "Live OHLCV retrieved successfully via yfinance.",
                    "is_mocked": False
                }
            except Exception as e:
                logger.error(f"Error fetching OHLCV from yfinance: {str(e)}")
                return {"error": "Failed to retrieve OHLCV from yfinance."}
        
        else:
            return {"error": f"Unsupported provider: {self.provider}"}

    async def test_universe_ohlcv_sample(self, limit: int = 5):
        enabled = os.getenv("ENABLE_OHLCV_DIAGNOSTICS", "false").lower() == "true"
        if not enabled:
            return {"error": "OHLCV Diagnostics are disabled (ENABLE_OHLCV_DIAGNOSTICS=false)."}
            
        md_enabled = os.getenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"
        if not md_enabled:
            return {"error": "Market Data smoke tests are disabled."}

        min_required = int(os.getenv("OHLCV_MIN_REQUIRED_BARS", "120"))
        lookback_days = int(os.getenv("OHLCV_LOOKBACK_DAYS", "180"))
        
        universe = self.get_symbol_map()[:limit]
        results = []
        
        for item in universe:
            ohlcv_res = await self.test_historical_ohlcv(item["yfinance_symbol"], lookback_days)
            
            if "error" in ohlcv_res:
                results.append({
                    "ticker": item["internal_ticker"],
                    "provider_ticker": "N/A",
                    "provider": self.provider,
                    "status": "failed",
                    "bars_returned": None,
                    "min_required_bars": min_required,
                    "latest_close": None,
                    "latest_volume": None,
                    "is_mocked": None,
                    "safe_message": ohlcv_res["error"]
                })
            else:
                results.append({
                    "ticker": item["internal_ticker"],
                    "provider_ticker": ohlcv_res.get("provider_ticker"),
                    "provider": ohlcv_res.get("provider"),
                    "status": ohlcv_res.get("status", "success"),
                    "bars_returned": ohlcv_res.get("bars_returned"),
                    "min_required_bars": ohlcv_res.get("min_required_bars"),
                    "has_open": ohlcv_res.get("has_open"),
                    "has_high": ohlcv_res.get("has_high"),
                    "has_low": ohlcv_res.get("has_low"),
                    "has_close": ohlcv_res.get("has_close"),
                    "has_volume": ohlcv_res.get("has_volume"),
                    "latest_close": ohlcv_res.get("latest_close"),
                    "latest_volume": ohlcv_res.get("latest_volume"),
                    "is_mocked": ohlcv_res.get("is_mocked"),
                    "safe_message": ohlcv_res.get("safe_message")
                })
                
        return {"success": True, "results": results}

    async def test_sample_quote(self, ticker: str):
        if not ticker:
            ticker = self.sample_ticker

        enabled = os.getenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false").lower() == "true"
        if not enabled:
            return {"error": "Smoke tests are disabled (ENABLE_MARKET_DATA_SMOKE_TESTS=false)."}

        status = await self.get_provider_status()
        if not status["configured"]:
            return {"error": status["safe_message"]}

        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        input_ticker = ticker
        
        if self.provider == "mock":
            # Return a realistic looking mocked price
            price = round(random.uniform(50.0, 150.0), 2)
            return {
                "input_ticker": input_ticker,
                "provider_ticker": input_ticker,
                "provider": "mock",
                "timestamp": current_time,
                "price": price,
                "currency": "SAR",
                "is_mocked": True,
                "message": "Mock quote generated successfully."
            }
            
        elif self.provider == "twelvedata":
            provider_ticker = input_ticker
            if provider_ticker.endswith(".SR"):
                provider_ticker = provider_ticker.replace(".SR", "") + ":Tadawul"
                
            api_key = os.getenv("TWELVEDATA_API_KEY", "")
            url = f"https://api.twelvedata.com/price?symbol={provider_ticker}&apikey={api_key}"
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, timeout=10.0)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    if "price" in data:
                        return {
                            "input_ticker": input_ticker,
                            "provider_ticker": provider_ticker,
                            "provider": "twelvedata",
                            "timestamp": current_time,
                            "price": float(data["price"]),
                            "currency": "Unknown", 
                            "is_mocked": False,
                            "message": "Live quote retrieved successfully."
                        }
                    else:
                        safe_error = data.get("message", "Unknown API format.")
                        if "403" in str(safe_error) or "plan" in str(safe_error).lower() or "access" in str(safe_error).lower() or "permission" in str(safe_error).lower():
                            return {"error": "TwelveData may require Tadawul access on your plan."}
                        return {"error": "Provider rejected the symbol or access is not available for this plan."}
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTPStatusError from TwelveData: {e.response.status_code}")
                return {"error": "Provider rejected the symbol or access is not available for this plan."}
            except Exception as e:
                logger.error(f"Error fetching from TwelveData: {str(e)}")
                return {"error": "Provider rejected the symbol or access is not available for this plan."}

        elif self.provider == "yfinance":
            provider_ticker = input_ticker
            try:
                import yfinance as yf
                import asyncio
                
                def fetch_yf(t):
                    ticker_obj = yf.Ticker(t)
                    info = ticker_obj.info
                    price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
                    currency = info.get("currency", "Unknown")
                    if price is None:
                        raise ValueError("Price not found in yfinance info.")
                    return price, currency

                price, currency = await asyncio.to_thread(fetch_yf, provider_ticker)
                return {
                    "input_ticker": input_ticker,
                    "provider_ticker": provider_ticker,
                    "provider": "yfinance",
                    "timestamp": current_time,
                    "price": float(price),
                    "currency": currency,
                    "is_mocked": False,
                    "message": "Live quote retrieved successfully via yfinance."
                }
            except Exception as e:
                logger.error(f"Error fetching from yfinance: {str(e)}")
                return {"error": "Failed to retrieve quote from yfinance."}
        
        else:
            return {"error": f"Unsupported provider: {self.provider}"}
