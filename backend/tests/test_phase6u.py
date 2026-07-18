import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.core.execution_guard import assert_no_execution_allowed, ExecutionNotAllowedError

@pytest.mark.asyncio
async def test_live_preview_status_locked():
    os.environ.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/system/live-preview-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["can_manual_analyze_preview"] is False
        assert data["can_manual_scout_preview"] is False
        assert data["safety_state"] == "SAFE"

@pytest.mark.asyncio
async def test_analyze_and_scout_locked_by_default():
    os.environ.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Assuming endpoints require auth, but they check environment first
        resp1 = await ac.post("/api/live-preview/analyze/2222")
        assert resp1.status_code in [400, 401, 403]
        
        resp2 = await ac.post("/api/live-preview/scout")
        assert resp2.status_code in [400, 401, 403]

@pytest.mark.asyncio
async def test_analyze_enabled_only():
    os.environ.clear()
    os.environ["ENABLE_LIVE_ANALYZE_PREVIEW"] = "true"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/system/live-preview-status")
        data = resp.json()
        assert data["can_manual_analyze_preview"] is True
        assert data["can_manual_scout_preview"] is False
        assert data["safety_state"] == "SAFE"

@pytest.mark.asyncio
async def test_scout_enabled_only():
    os.environ.clear()
    os.environ["ENABLE_LIVE_SCOUT_PREVIEW"] = "true"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/system/live-preview-status")
        data = resp.json()
        assert data["can_manual_analyze_preview"] is False
        assert data["can_manual_scout_preview"] is True
        assert data["safety_state"] == "SAFE"

@pytest.mark.asyncio
async def test_scheduler_blocks_preview():
    os.environ.clear()
    os.environ["ENABLE_LIVE_ANALYZE_PREVIEW"] = "true"
    os.environ["ENABLE_ALERT_SCHEDULER"] = "true"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/system/live-preview-status")
        data = resp.json()
        assert data["can_manual_analyze_preview"] is False
        assert data["safety_state"] == "UNSAFE"
        assert "Scheduler must be disabled" in data["locked_reason"]

@pytest.mark.asyncio
async def test_provider_coverage_blocks_preview():
    os.environ.clear()
    os.environ["ENABLE_LIVE_SCOUT_PREVIEW"] = "true"
    os.environ["ENABLE_PROVIDER_COVERAGE_SCAN"] = "true"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/system/live-preview-status")
        data = resp.json()
        assert data["can_manual_scout_preview"] is False
        assert data["safety_state"] == "UNSAFE"
        assert "Provider coverage scan must be disabled" in data["locked_reason"]

def test_execution_guard_blocks():
    with pytest.raises(ExecutionNotAllowedError):
        assert_no_execution_allowed()

@pytest.mark.asyncio
async def test_safety_matrix_default_safe():
    os.environ.clear()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/system/safety-matrix")
        assert resp.status_code == 200
        data = resp.json()
        assert data["safety_state"] == "SAFE"
        assert "production_db_path" not in data or data["production_db_path_configured"] is False
