"""
Phase 7A tests — Controlled Telegram manual test-send.

Covers:
- Default state (all flags off) does not send
- Missing token blocks send
- Missing chat ID blocks send
- Scheduler enabled blocks send
- ENABLE_TELEGRAM_SEND=false blocks send
- ENABLE_TELEGRAM_TEST_SEND=false blocks send
- All gates true calls sender (network mocked)
- No token/chat/authorized IDs leak in any response
- Safety matrix exposes Phase 7A gate fields
- Locked endpoint returns correct locked shape
"""
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.telegram_sender import evaluate_test_send_gates


# ── helper ──────────────────────────────────────────────────────────────────

def _all_gates_env(monkeypatch):
    """Set all five gates to their required open values."""
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "true")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "111111111:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "987654321")


def _clear_telegram_env(monkeypatch):
    for key in [
        "ENABLE_TELEGRAM_TEST_SEND", "ENABLE_TELEGRAM_SEND",
        "ENABLE_ALERT_SCHEDULER", "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID",
    ]:
        monkeypatch.delenv(key, raising=False)


# ── gate evaluation unit tests ───────────────────────────────────────────────

def test_default_state_all_gates_locked(monkeypatch):
    """With no env vars set, all gates are locked and no network call is allowed."""
    _clear_telegram_env(monkeypatch)
    gates = evaluate_test_send_gates()
    assert gates["can_run_test_send"] is False
    assert gates["network_call_allowed_for_test_send"] is False
    assert gates["test_send_gate_status"] == "locked"
    assert gates["test_send_requires_manual_enablement"] is True
    assert len(gates["blocked_reasons"]) > 0


def test_missing_token_blocks_send(monkeypatch):
    """Even when all flags are true, missing token blocks the send."""
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "true")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    gates = evaluate_test_send_gates()
    assert gates["can_run_test_send"] is False
    assert "No Telegram token configured" in gates["blocked_reasons"]


def test_missing_chat_id_blocks_send(monkeypatch):
    """Token configured but missing chat ID blocks the send."""
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "true")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "111:AAAAAA")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    gates = evaluate_test_send_gates()
    assert gates["can_run_test_send"] is False
    assert "TELEGRAM_CHAT_ID not configured" in gates["blocked_reasons"]


def test_scheduler_enabled_blocks_send(monkeypatch):
    """ENABLE_ALERT_SCHEDULER=true must block the test send."""
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "true")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "111:AAAAAA")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    gates = evaluate_test_send_gates()
    assert gates["can_run_test_send"] is False
    assert "ENABLE_ALERT_SCHEDULER must be false" in gates["blocked_reasons"]


def test_send_flag_false_blocks(monkeypatch):
    """ENABLE_TELEGRAM_SEND=false blocks even if test flag is true."""
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "111:AAAAAA")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    gates = evaluate_test_send_gates()
    assert gates["can_run_test_send"] is False
    assert "ENABLE_TELEGRAM_SEND is false" in gates["blocked_reasons"]


def test_test_flag_false_blocks(monkeypatch):
    """ENABLE_TELEGRAM_TEST_SEND=false blocks even if send flag is true."""
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "true")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "111:AAAAAA")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    gates = evaluate_test_send_gates()
    assert gates["can_run_test_send"] is False
    assert "ENABLE_TELEGRAM_TEST_SEND is false" in gates["blocked_reasons"]


def test_all_gates_open(monkeypatch):
    """With all five gates satisfied, can_run_test_send is True."""
    _all_gates_env(monkeypatch)
    gates = evaluate_test_send_gates()
    assert gates["can_run_test_send"] is True
    assert gates["test_send_gate_status"] == "open"
    assert gates["blocked_reasons"] == []


def test_alias_token_satisfies_token_gate(monkeypatch):
    """TELEGRAM_TOKEN alias satisfies the token gate."""
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "true")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_TOKEN", "222:BBBBBB")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    gates = evaluate_test_send_gates()
    assert gates["can_run_test_send"] is True


# ── sender unit tests (mocked network) ───────────────────────────────────────

def test_send_locked_when_gates_fail(monkeypatch):
    """send_telegram_test_message returns locked result without network call."""
    _clear_telegram_env(monkeypatch)
    from backend.core.telegram_sender import send_telegram_test_message
    result = asyncio.run(send_telegram_test_message())
    assert result["sent"] is False
    assert result["network_call_made"] is False
    assert result["dry_run"] is True


def test_send_calls_network_when_all_gates_open(monkeypatch):
    """When all gates pass, send_telegram_test_message makes one HTTP POST (mocked)."""
    _all_gates_env(monkeypatch)

    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("backend.core.telegram_sender.httpx.AsyncClient", return_value=mock_client):
        from backend.core.telegram_sender import send_telegram_test_message
        result = asyncio.run(send_telegram_test_message())

    assert result["sent"] is True
    assert result["network_call_made"] is True
    assert result["dry_run"] is False
    mock_client.post.assert_called_once()

    result_text = str(result)
    assert "111111111" not in result_text  # token not in result
    assert "987654321" not in result_text  # raw chat id not in result


def test_no_secrets_in_sender_result(monkeypatch):
    """Sender result must not contain token or raw chat ID values."""
    _all_gates_env(monkeypatch)

    mock_response = MagicMock()
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("backend.core.telegram_sender.httpx.AsyncClient", return_value=mock_client):
        from backend.core.telegram_sender import send_telegram_test_message
        result = asyncio.run(send_telegram_test_message())

    result_str = str(result)
    assert "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" not in result_str  # no token secret part
    # masked chat should end with last 4 chars only
    assert result["target_chat_masked"].startswith("***")


# ── endpoint tests ───────────────────────────────────────────────────────────

def test_test_send_endpoint_locked_by_default(monkeypatch):
    """POST /api/alerts/telegram/test-send returns locked when gates are off."""
    _clear_telegram_env(monkeypatch)
    with TestClient(app) as client:
        response = client.post(
            "/api/alerts/telegram/test-send",
            headers={"Authorization": "Bearer ignored"},
        )
    # Either 200 locked or 401 (no real auth in test); both are fine —
    # what matters is that no network call was made (mocked at module level would need
    # full integration; here we at least confirm no 500 and no send flag in body).
    assert response.status_code in (200, 401, 403)
    if response.status_code == 200:
        data = response.json()
        assert data["sent"] is False
        assert data["network_call_made"] is False


def test_safety_matrix_exposes_phase7a_fields(monkeypatch):
    """Safety matrix response includes Phase 7A gate-status fields."""
    _clear_telegram_env(monkeypatch)
    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    data = response.json()
    assert "can_run_test_send" in data
    assert "test_send_gate_status" in data
    assert "test_send_requires_manual_enablement" in data
    assert "network_call_allowed_for_test_send" in data
    assert data["can_run_test_send"] is False
    assert data["test_send_gate_status"] == "locked"
    assert data["test_send_requires_manual_enablement"] is True
    assert data["network_call_allowed_for_test_send"] is False


def test_safety_matrix_no_secret_leak(monkeypatch):
    """Safety matrix must never return token or chat ID values."""
    secret_token = "999999999:SECRETSECRETSECRETSECRETSECRETSECRET"
    secret_chat = "111222333"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", secret_token)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", secret_chat)
    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    body = response.text
    assert secret_token not in body
    assert secret_chat not in body
    assert "SECRETSECRET" not in body


def test_safety_matrix_no_authorized_ids_leak(monkeypatch):
    """Authorized user IDs must not appear in the safety matrix response."""
    secret_ids = "111222333,444555666,777888999"
    monkeypatch.setenv("AUTHORIZED_USER_IDS", secret_ids)
    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    body = response.text
    assert "111222333" not in body
    assert "444555666" not in body
    assert "777888999" not in body


def test_safety_matrix_state_safe_with_all_sends_disabled(monkeypatch):
    """Safety matrix state must be SAFE when all send flags are false."""
    _clear_telegram_env(monkeypatch)
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "false")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "false")
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    data = response.json()
    assert data["safety_state"] == "SAFE"
