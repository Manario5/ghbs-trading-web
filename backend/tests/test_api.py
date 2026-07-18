import os
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import aiosqlite

from backend.main import app
from backend.auth.security import get_password_hash

# Note: this file relies on the DB_PATH from the env or falling back to tasi_ledger_test.db
# We'll set an environment variable or simply rely on the default in db config.

import pytest_asyncio

@pytest_asyncio.fixture(autouse=True, loop_scope="function")
async def setup_db(monkeypatch):
    monkeypatch.setenv("DB_PATH", "test_api.db")
    # Setup test DB specifically
    from backend.db.database import init_db
    await init_db()
    
    async with aiosqlite.connect("test_api.db") as db:
        pwd_hash = get_password_hash("password123")
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username, password_hash, role, created_at)
            VALUES (1, 'admin', ?, 'admin', ?)
        """, (pwd_hash, datetime.now(timezone.utc).isoformat()))
        await db.commit()

    yield
    
    if os.path.exists("test_api.db"):
        os.remove("test_api.db")

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/system/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_auth_and_protected_routes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login
        response = await ac.post("/api/auth/login", data={"username": "admin", "password": "password123"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Access protected route
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = await ac.get("/api/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "admin"
        
        # Access setups
        setup_resp = await ac.get("/api/setups/", headers=headers)
        assert setup_resp.status_code == 200
        assert isinstance(setup_resp.json(), list)

@pytest.mark.asyncio
async def test_stubbed_engine_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Need auth first
        login_resp = await ac.post("/api/auth/login", data={"username": "admin", "password": "password123"})
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        analyze_resp = await ac.post("/api/analyze/7203", headers=headers)
        assert analyze_resp.status_code == 200
        assert analyze_resp.json()["mocked_data"] is True
        
        scout_resp = await ac.post("/api/scout/run", headers=headers)
        assert scout_resp.status_code == 200
        assert scout_resp.json()["mocked_data"] is True
