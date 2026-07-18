import os
from fastapi.testclient import TestClient
from backend.main import app

def test_secret_status_endpoint_no_secrets(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("TWELVEDATA_API_KEY", raising=False)
    monkeypatch.delenv("SAHMK_API_KEY", raising=False)
    monkeypatch.delenv("TRADINGVIEW_API_KEY", raising=False)
    
    with TestClient(app) as client:
        response = client.get("/api/system/secret-status")
        assert response.status_code == 200
        data = response.json()
        assert data["anthropic"]["configured"] is False
        assert data["telegram"]["bot_token_configured"] is False
        assert data["telegram"]["ready_for_notifications"] is False
        assert data["summary"]["any_secrets_configured"] is False

def test_secret_status_endpoint_whitespace_is_missing(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "  ")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", " \n ")
    
    with TestClient(app) as client:
        response = client.get("/api/system/secret-status")
        assert response.status_code == 200
        data = response.json()
        assert data["anthropic"]["configured"] is False
        assert data["telegram"]["bot_token_configured"] is False

def test_secret_status_endpoint_dummy_values_return_booleans_only(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy1")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy2")
    
    with TestClient(app) as client:
        response = client.get("/api/system/secret-status")
        assert response.status_code == 200
        data = response.json()
        assert data["anthropic"]["configured"] is True
        assert data["telegram"]["bot_token_configured"] is True
        # Ensure no values are leaked
        response_text = response.text
        assert "dummy1" not in response_text
        assert "dummy2" not in response_text

def test_safety_matrix_remains_unchanged(monkeypatch):
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "false")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy-token")
    
    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
        assert response.status_code == 200
        data = response.json()
        assert data["safety_state"] == "SAFE"
        assert data["telegram_configured_masked"] == "configured"
        assert "dummy-token" not in response.text
