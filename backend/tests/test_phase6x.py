import json
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.telegram_readiness import get_telegram_alert_status
from backend.core.secrets import get_secret_status


def test_telegram_token_alias_used_when_primary_missing(monkeypatch):
    fake_alias = "123456789:" + ("A" * 35)
    fake_chat = "987654321"
    fake_ids = "111,222,333"

    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_TOKEN", fake_alias)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", fake_chat)
    monkeypatch.setenv("AUTHORIZED_USER_IDS", fake_ids)
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")

    status = get_telegram_alert_status()
    text = json.dumps(status)

    assert status["telegram_bot_token_configured"] is True
    assert status["telegram_token_source"] == "TELEGRAM_TOKEN"
    assert status["telegram_token_alias_configured"] is True
    assert status["telegram_token_alias_used"] is True
    assert status["authorized_user_ids_configured"] is True
    assert status["authorized_user_ids_masked"] == "configured"
    assert status["authorized_user_ids_count"] == 3
    assert status["telegram_network_calls_locked"] is True
    assert status["can_send_telegram"] is False
    assert status["safety_state"] == "SAFE"

    assert fake_alias not in text
    assert fake_chat not in text
    assert "111" not in text
    assert "222" not in text
    assert "333" not in text


def test_primary_telegram_bot_token_takes_precedence(monkeypatch):
    fake_primary = "123456789:" + ("B" * 35)
    fake_alias = "123456789:" + ("C" * 35)

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", fake_primary)
    monkeypatch.setenv("TELEGRAM_TOKEN", fake_alias)
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")

    status = get_telegram_alert_status()
    text = json.dumps(status)

    assert status["telegram_token_source"] == "TELEGRAM_BOT_TOKEN"
    assert status["telegram_token_alias_configured"] is True
    assert status["telegram_token_alias_used"] is False
    assert status["telegram_network_calls_locked"] is True
    assert status["can_send_telegram"] is False

    assert fake_primary not in text
    assert fake_alias not in text


def test_secret_status_masks_anthropic_and_telegram_alias(monkeypatch):
    fake_anthropic = "sk-ant-api03-" + ("D" * 40)
    fake_alias = "123456789:" + ("E" * 35)
    fake_chat = "987654321"
    fake_ids = "111,222,333"

    monkeypatch.setenv("ANTHROPIC_API_KEY", fake_anthropic)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_TOKEN", fake_alias)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", fake_chat)
    monkeypatch.setenv("AUTHORIZED_USER_IDS", fake_ids)

    status = get_secret_status()
    text = json.dumps(status)

    assert status["anthropic"]["configured"] is True
    assert status["anthropic"]["masked"] == "configured"
    assert status["telegram"]["bot_token_configured"] is True
    assert status["telegram"]["bot_token_masked"] == "configured"
    assert status["telegram"]["token_source"] == "TELEGRAM_TOKEN"
    assert status["telegram"]["token_alias_used"] is True
    assert status["telegram"]["chat_id_masked"] == "configured"
    assert status["telegram"]["authorized_user_ids_masked"] == "configured"
    assert status["telegram"]["authorized_user_ids_count"] == 3
    assert status["telegram"]["ready_for_notifications"] is True

    assert fake_anthropic not in text
    assert fake_alias not in text
    assert fake_chat not in text
    assert "111" not in text
    assert "222" not in text
    assert "333" not in text


def test_secret_status_endpoint_does_not_leak_values(monkeypatch):
    fake_anthropic = "sk-ant-api03-" + ("F" * 40)
    fake_alias = "123456789:" + ("G" * 35)
    fake_chat = "987654321"
    fake_ids = "111,222,333"

    monkeypatch.setenv("ANTHROPIC_API_KEY", fake_anthropic)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_TOKEN", fake_alias)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", fake_chat)
    monkeypatch.setenv("AUTHORIZED_USER_IDS", fake_ids)

    with TestClient(app) as client:
        response = client.get("/api/system/secret-status")

    assert response.status_code == 200
    body = response.text
    data = response.json()

    assert data["anthropic"]["masked"] == "configured"
    assert data["telegram"]["token_source"] == "TELEGRAM_TOKEN"
    assert data["telegram"]["authorized_user_ids_count"] == 3

    assert fake_anthropic not in body
    assert fake_alias not in body
    assert fake_chat not in body
    assert "111" not in body
    assert "222" not in body
    assert "333" not in body


def test_safety_matrix_6x_fields_are_safe(monkeypatch):
    fake_alias = "123456789:" + ("H" * 35)

    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "false")
    monkeypatch.setenv("DB_PATH", "tasi_ledger_test.db")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "false")
    monkeypatch.setenv("ENABLE_LIVE_SCOUT_PREVIEW", "false")
    monkeypatch.setenv("ENABLE_PROVIDER_COVERAGE_SCAN", "false")
    monkeypatch.setenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_TOKEN", fake_alias)
    monkeypatch.setenv("AUTHORIZED_USER_IDS", "111,222,333")

    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")

    assert response.status_code == 200
    body = response.text
    data = response.json()

    assert data["safety_state"] == "SAFE"
    assert data["telegram_token_source"] == "TELEGRAM_TOKEN"
    assert data["telegram_token_alias_used"] is True
    assert data["authorized_user_ids_masked"] == "configured"
    assert data["authorized_user_ids_count"] == 3
    assert data["telegram_network_calls_locked"] is True

    assert fake_alias not in body
    assert "111" not in body
    assert "222" not in body
    assert "333" not in body
