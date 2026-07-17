import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import aiosqlite
from datetime import datetime, timezone
from backend.main import app
from backend.auth.security import get_password_hash

@pytest_asyncio.fixture(autouse=True, loop_scope="function")
async def setup_db(monkeypatch):
    monkeypatch.setenv("DB_PATH", "test_api_v2b.db")
    from backend.db.database import init_db
    await init_db()
    
    async with aiosqlite.connect("test_api_v2b.db") as db:
        pwd_hash = get_password_hash("password123")
        await db.execute("""
            INSERT OR IGNORE INTO users (id, username, password_hash, role, created_at)
            VALUES (1, 'admin', ?, 'admin', ?)
        """, (pwd_hash, datetime.now(timezone.utc).isoformat()))
        await db.commit()

    yield
    
    if os.path.exists("test_api_v2b.db"):
        try:
            os.remove("test_api_v2b.db")
        except:
            pass

@pytest_asyncio.fixture
async def auth_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", data={"username": "admin", "password": "password123"})
        return response.json()["access_token"]

@pytest.mark.asyncio
async def test_analyze_sandbox(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = await ac.post("/api/analyze/2222", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["mocked_data"] is True
        assert data["external_api_calls"] is False
        assert "setup_type" in data
        assert "proposal" in data

@pytest.mark.asyncio
async def test_scout_sandbox(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = await ac.post("/api/scout/run", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["mocked_data"] is True
        assert data["fetched"] > 0
        assert "actionable" in data

@pytest.mark.asyncio
async def test_trade_endpoints_sandbox(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {auth_token}"}
        # Buy
        buy_resp = await ac.post("/api/trades/buy", json={"ticker": "2222", "price": 50.0, "qty": 100}, headers=headers)
        assert buy_resp.status_code == 200
        buy_data = buy_resp.json()
        assert buy_data["sandbox_mode"] is True
        assert buy_data["success"] is True
        pos_id = buy_data["position_id"]
        
        # Check audit event
        async with aiosqlite.connect("test_api_v2b.db") as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM audit_events ORDER BY id DESC") as cur:
                audit = await cur.fetchone()
                assert audit is not None
                assert audit["action_type"] == "SANDBOX_BUY"
        
        # Sell
        sell_resp = await ac.post("/api/trades/sell", json={"ticker": "2222", "price": 55.0, "qty": 50}, headers=headers)
        assert sell_resp.status_code == 200
        sell_data = sell_resp.json()
        assert sell_data["sandbox_mode"] is True

@pytest.mark.asyncio
async def test_risk_can_i_take_this_trade(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = await ac.post("/api/risk/can-i-take-this-trade", json={"ticker": "2222", "entry_price": 50.0, "qty": 10}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["sandbox_mode"] is True
        assert data["pass"] is True
        assert "risk_sar" in data

@pytest.mark.asyncio
async def test_no_delete_endpoint(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = await ac.delete("/api/trades/delete/1", headers=headers)
        assert resp.status_code == 404
