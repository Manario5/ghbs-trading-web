"""Phase 6Z tests: telegram_configured_masked respects TELEGRAM_TOKEN alias."""
import json
from fastapi.testclient import TestClient

from backend.main import app


def test_telegram_configured_masked_via_primary(monkeypatch):
    """telegram_configured_masked is 'configured' when TELEGRAM_BOT_TOKEN is set."""
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy-primary-token")

    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_configured_masked"] == "configured"
    assert "dummy-primary-token" not in response.text


def test_telegram_configured_masked_via_alias(monkeypatch):
    """telegram_configured_masked is 'configured' when only TELEGRAM_TOKEN alias is set."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_TOKEN", "dummy-alias-token")

    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_configured_masked"] == "configured"
    assert "dummy-alias-token" not in response.text


def test_telegram_configured_masked_when_neither_set(monkeypatch):
    """telegram_configured_masked is 'not configured' when no token is set."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)

    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_configured_masked"] == "not configured"


def test_telegram_configured_masked_whitespace_alias_is_missing(monkeypatch):
    """Whitespace-only TELEGRAM_TOKEN does not count as configured."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_TOKEN", "   ")

    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_configured_masked"] == "not configured"


def test_no_secret_values_in_safety_matrix_response(monkeypatch):
    """Actual token values must never appear in safety-matrix JSON response."""
    secret_primary = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
    secret_alias = "987654321:ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvu"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", secret_primary)
    monkeypatch.setenv("TELEGRAM_TOKEN", secret_alias)

    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    body = response.text
    assert secret_primary not in body
    assert secret_alias not in body


def test_no_secret_values_in_secret_status_response(monkeypatch):
    """Actual token/key values must never appear in secret-status JSON response."""
    secret_token = "tok-supersecret-value-12345"
    secret_anthropic = "sk-ant-supersecret-value-67890"
    monkeypatch.setenv("TELEGRAM_TOKEN", secret_token)
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret_anthropic)

    with TestClient(app) as client:
        response = client.get("/api/system/secret-status")
    assert response.status_code == 200
    body = response.text
    assert secret_token not in body
    assert secret_anthropic not in body
