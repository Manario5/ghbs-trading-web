import os
import pytest
from httpx import AsyncClient, ASGITransport
import aiosqlite
from datetime import datetime, timezone
from backend.main import app
from backend.auth.security import get_password_hash

# Need loop_scope to match fixture in this pytest_asyncio version
@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "true")
    monkeypatch.setenv("ENABLE_LIVE_SCOUT_PREVIEW", "true")
    monkeypatch.setenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "true")
    monkeypatch.setenv("ENABLE_OHLCV_DIAGNOSTICS", "true")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "mock")

import pytest_asyncio

@pytest_asyncio.fixture(autouse=True, loop_scope="function")
async def setup_db(monkeypatch):
    monkeypatch.setenv("DB_PATH", "test_live_preview.db")
    from backend.db.database import init_db
    await init_db()
    
    async with aiosqlite.connect("test_live_preview.db") as db:
        pwd_hash = get_password_hash("password123")
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username, password_hash, role, created_at)
            VALUES (1, 'admin', ?, 'admin', ?)
        """, (pwd_hash, datetime.now(timezone.utc).isoformat()))
        await db.commit()

    yield
    
    if os.path.exists("test_live_preview.db"):
        os.remove("test_live_preview.db")

@pytest.mark.asyncio
async def test_live_preview_nan_serialization():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_resp = await ac.post("/api/auth/login", data={"username": "admin", "password": "password123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test Live Preview Sandbox
        resp = await ac.post("/api/live-preview/analyze/2222", headers=headers)
        # Should not throw a serialization error internally
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None
        assert data["sandbox_only"] == True
        assert data["execution_allowed"] == False

@pytest.mark.asyncio
async def test_live_preview_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "false")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_resp = await ac.post("/api/auth/login", data={"username": "admin", "password": "password123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = await ac.post("/api/live-preview/analyze/2222", headers=headers)
        assert resp.status_code == 400
        assert "disabled" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_live_preview_invalid_ticker():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_resp = await ac.post("/api/auth/login", data={"username": "admin", "password": "password123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = await ac.post("/api/live-preview/analyze/INVALIDXXX", headers=headers)
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_safety_matrix_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_resp = await ac.post("/api/auth/login", data={"username": "admin", "password": "password123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await ac.get("/api/system/safety-matrix", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "safety_state" in data
        assert "allow_production_db" in data
        assert data["safety_state"] in ["SAFE", "WARNING", "UNSAFE"]
