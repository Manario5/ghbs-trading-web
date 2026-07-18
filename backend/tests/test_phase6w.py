import json
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.telegram_readiness import (
    get_telegram_alert_status,
    build_telegram_dry_run_preview,
)


def test_telegram_default_locked_state(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setenv("ENABLE_TELEGRAM_DRY_RUN", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")

    status = get_telegram_alert_status()

    assert status["telegram_bot_token_configured"] is False
    assert status["telegram_chat_id_configured"] is False
    assert status["telegram_dry_run_enabled"] is True
    assert status["telegram_send_enabled"] is False
    assert status["telegram_test_send_enabled"] is False
    assert status["can_send_telegram"] is False
    assert status["can_run_test_send"] is False
    assert status["telegram_network_calls_locked"] is True
    assert status["safety_state"] == "SAFE"


def test_telegram_configured_values_are_masked(monkeypatch):
    fake_token = "123456789:" + ("A" * 35)
    fake_chat = "987654321"

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", fake_token)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", fake_chat)
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")

    status = get_telegram_alert_status()
    serialized = json.dumps(status)

    assert status["telegram_bot_token_configured"] is True
    assert status["telegram_chat_id_configured"] is True
    assert status["telegram_bot_token_masked"] == "configured"
    assert status["telegram_chat_id_masked"] == "configured"
    assert fake_token not in serialized
    assert fake_chat not in serialized
    assert status["can_send_telegram"] is False


def test_telegram_status_endpoint_safe(monkeypatch):
    fake_token = "123456789:" + ("B" * 35)
    fake_chat = "1122334455"

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", fake_token)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", fake_chat)
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")

    with TestClient(app) as client:
        response = client.get("/api/system/telegram-alert-status")

    assert response.status_code == 200
    body = response.text
    data = response.json()

    assert data["telegram_bot_token_masked"] == "configured"
    assert data["telegram_chat_id_masked"] == "configured"
    assert data["telegram_network_calls_locked"] is True
    assert data["can_send_telegram"] is False
    assert fake_token not in body
    assert fake_chat not in body


def test_telegram_dry_run_preview_never_sends(monkeypatch):
    monkeypatch.setenv("ENABLE_TELEGRAM_DRY_RUN", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")

    preview = build_telegram_dry_run_preview({
        "template_type": "setup_alert",
        "ticker": "2222",
        "signal": "WATCH",
        "setup_type": "DRY_RUN_TEST",
    })

    assert preview["dry_run"] is True
    assert preview["would_send"] is False
    assert preview["execution_allowed"] is False
    assert preview["telegram_send_enabled"] is False
    assert preview["telegram_test_send_enabled"] is False
    assert preview["telegram_network_calls_locked"] is True
    assert preview["safety_state"] == "SAFE"


def test_safety_matrix_includes_telegram_fields(monkeypatch):
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "false")
    monkeypatch.setenv("ENABLE_LIVE_SCOUT_PREVIEW", "false")
    monkeypatch.setenv("ENABLE_PROVIDER_COVERAGE_SCAN", "false")
    monkeypatch.setenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_DRY_RUN", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")

    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")

    assert response.status_code == 200
    data = response.json()

    assert data["safety_state"] == "SAFE"
    assert data["telegram_dry_run_enabled"] is True
    assert data["telegram_send_enabled"] is False
    assert data["telegram_test_send_enabled"] is False
    assert data["telegram_network_calls_locked"] is True
    assert data["telegram_readiness_safe"] is True
    assert data["provider_calls_locked"] is True
    assert data["production_db_readonly_gate_enabled"] is False
