import os
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from backend.auth.dependencies import get_current_user
from backend.db.database import get_db
from backend.services.market_data_service import MarketDataService

router = APIRouter()

class TestQuoteRequest(BaseModel):
    ticker: Optional[str] = None

class StatusResponse(BaseModel):
    provider_name: str
    configured: bool
    enabled: bool
    sample_ticker: str
    safe_message: str

class QuoteResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class TestUniverseRequest(BaseModel):
    limit: Optional[int] = 5

@router.get("/provider-health")
async def provider_health(current_user: dict = Depends(get_current_user)):
    """Config-only provider health + fallback report (Release Train C). No network calls."""
    from backend.core.provider_health import get_provider_health
    return get_provider_health()

@router.get("/symbol-map")
async def get_symbol_map(current_user: dict = Depends(get_current_user)):
    service = MarketDataService()
    return service.get_symbol_map()

@router.post("/test-universe-sample")
async def test_universe_sample(req: dict = None, current_user: dict = Depends(get_current_user)):
    limit = req.get("limit", 5) if req else 5
    service = MarketDataService()
    res = await service.test_universe_sample(limit)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

class TestOhlcvRequest(BaseModel):
    ticker: Optional[str] = None
    lookback_days: Optional[int] = None

@router.post("/test-ohlcv")
async def test_ohlcv(req: TestOhlcvRequest, current_user: dict = Depends(get_current_user)):
    service = MarketDataService()
    ticker = req.ticker or service.sample_ticker
    lookback = req.lookback_days or int(os.getenv("OHLCV_LOOKBACK_DAYS", "180"))
    
    res = await service.test_historical_ohlcv(ticker, lookback)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/test-universe-ohlcv-sample")
async def test_universe_ohlcv_sample(req: dict = None, current_user: dict = Depends(get_current_user)):
    limit = req.get("limit", 5) if req else 5
    service = MarketDataService()
    res = await service.test_universe_ohlcv_sample(limit)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/provider-coverage-scan")
async def provider_coverage_scan(req: dict = None, current_user: dict = Depends(get_current_user)):
    service = MarketDataService()
    limit = req.get("limit", 80) if req else int(os.getenv("PROVIDER_COVERAGE_LIMIT", "80"))
    res = await service.run_provider_coverage_scan(limit)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.get("/provider-coverage-last")
async def get_provider_coverage_last(current_user: dict = Depends(get_current_user)):
    service = MarketDataService()
    res = await service.get_provider_coverage_last()
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.get("/status", response_model=StatusResponse)
async def get_market_data_status(current_user: dict = Depends(get_current_user)):
    service = MarketDataService()
    return await service.get_provider_status()

@router.post("/test-quote", response_model=QuoteResponse)
async def test_market_data_quote(req: TestQuoteRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    service = MarketDataService()
    ticker = req.ticker or service.sample_ticker

    quote_result = await service.test_sample_quote(ticker)
    
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    user_id = current_user.get("id")

    if "error" in quote_result:
        # Log failure
        await db.execute("""
            INSERT INTO audit_events (
                user_id, action_type, object_type, object_id, timestamp, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id, "market_data_test", "provider", ticker, current_time, 
            f"Failed: {quote_result['error']}"
        ))
        await db.commit()
        raise HTTPException(status_code=400, detail=quote_result["error"])

    # Log success
    await db.execute("""
        INSERT INTO audit_events (
            user_id, action_type, object_type, object_id, timestamp, notes
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id, "market_data_test", "provider", ticker, current_time, 
        f"Success. Price: {quote_result.get('price')} {quote_result.get('currency')} (Mocked: {quote_result.get('is_mocked')})"
    ))
    await db.commit()

    return QuoteResponse(
        success=True,
        data=quote_result,
        message=quote_result.get("message")
    )
