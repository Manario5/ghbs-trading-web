"""
Release Train A tests — Alerts & Telegram Completion.

Covers:
- Alert template registry: listing, rendering, unknown ids, placeholder safety
- File-based alert audit layer: write, read, sanitization, resilience
- /alerts/telegram/status endpoint auth requirement
- Test-send endpoint records audit entries when locked
- No secrets in templates, audit entries, or status responses
- Existing safety guarantees still hold (default locked, SAFE state)
"""
import asyncio
import json
import os
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

from backend.main import app
from backend.core.alert_templates import list_templates, render_template, TEMPLATES
from backend.core.alert_audit import (
    record_alert_attempt,
    read_recent_attempts,
    last_attempt,
    AUDIT_FILE_ENV,
)


# ── template registry ────────────────────────────────────────────────────────

def test_templates_list_shape():
    templates = list_templates()
    assert len(templates) >= 5
    for t in templates:
        assert set(t.keys()) == {"id", "title", "category", "body"}
        assert t["category"] in ("test", "system")


def test_templates_contain_no_secret_placeholders():
    """Template bodies must not reference token/chat/key placeholders."""
    for tid, t in TEMPLATES.items():
        body_lower = t["body"].lower()
        assert "token" not in body_lower, f"{tid} references token"
        assert "chat_id" not in body_lower, f"{tid} references chat_id"
        assert "api_key" not in body_lower, f"{tid} references api_key"


def test_render_known_template():
    result = render_template("setup_detected", {
        "ticker": "2222.SR", "signal": "BUY", "setup_type": "BOUNCE", "regime": "UPTREND",
    })
    assert result["known_template"] is True
    assert "2222.SR" in result["rendered"]
    assert "BOUNCE" in result["rendered"]


def test_render_unknown_template_does_not_raise():
    result = render_template("no_such_template")
    assert result["known_template"] is False
    assert result["rendered"] == ""


def test_render_missing_params_leaves_placeholders():
    result = render_template("tp_hit", {})
    assert result["known_template"] is True
    assert "{ticker}" in result["rendered"]
    assert "{level}" in result["rendered"]


def test_render_manual_test_send_fills_timestamp():
    result = render_template("manual_test_send")
    assert "{timestamp}" not in result["rendered"]
    assert "MANUAL TEST ONLY" in result["rendered"]


# ── audit layer ──────────────────────────────────────────────────────────────

def _use_tmp_audit(monkeypatch, tmp_path):
    audit_file = str(tmp_path / "audit_test.jsonl")
    monkeypatch.setenv(AUDIT_FILE_ENV, audit_file)
    return audit_file


def test_audit_write_and_read(monkeypatch, tmp_path):
    _use_tmp_audit(monkeypatch, tmp_path)
    assert record_alert_attempt({
        "kind": "test_send", "outcome": "locked",
        "gate_status": "locked", "network_call_made": False,
        "blocked_reasons": ["ENABLE_TELEGRAM_SEND is false"],
    }) is True
    entries = read_recent_attempts()
    assert len(entries) == 1
    assert entries[0]["kind"] == "test_send"
    assert entries[0]["outcome"] == "locked"
    assert entries[0]["network_call_made"] is False
    assert "timestamp" in entries[0]


def test_audit_newest_first(monkeypatch, tmp_path):
    _use_tmp_audit(monkeypatch, tmp_path)
    record_alert_attempt({"kind": "dry_run", "outcome": "locked"})
    record_alert_attempt({"kind": "test_send", "outcome": "locked"})
    entries = read_recent_attempts()
    assert entries[0]["kind"] == "test_send"
    assert entries[1]["kind"] == "dry_run"
    assert last_attempt()["kind"] == "test_send"


def test_audit_strips_unknown_fields(monkeypatch, tmp_path):
    """Fields outside the allowlist (e.g. accidental secrets) must be dropped."""
    audit_file = _use_tmp_audit(monkeypatch, tmp_path)
    record_alert_attempt({
        "kind": "test_send",
        "outcome": "locked",
        "bot_token": "SHOULD_NEVER_BE_WRITTEN",
        "chat_id": "1234567890",
    })
    raw = open(audit_file, encoding="utf-8").read()
    assert "SHOULD_NEVER_BE_WRITTEN" not in raw
    assert "1234567890" not in raw
    assert "bot_token" not in raw


def test_audit_read_missing_file_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setenv(AUDIT_FILE_ENV, str(tmp_path / "does_not_exist.jsonl"))
    assert read_recent_attempts() == []
    assert last_attempt() is None


def test_audit_skips_corrupt_lines(monkeypatch, tmp_path):
    audit_file = _use_tmp_audit(monkeypatch, tmp_path)
    with open(audit_file, "w", encoding="utf-8") as f:
        f.write("not-json\n")
        f.write(json.dumps({"kind": "dry_run", "outcome": "locked"}) + "\n")
    entries = read_recent_attempts()
    assert len(entries) == 1
    assert entries[0]["kind"] == "dry_run"


def test_audit_respects_limit(monkeypatch, tmp_path):
    _use_tmp_audit(monkeypatch, tmp_path)
    for i in range(30):
        record_alert_attempt({"kind": "dry_run", "outcome": "locked"})
    assert len(read_recent_attempts(limit=10)) == 10


# ── endpoints ────────────────────────────────────────────────────────────────

def test_telegram_status_endpoint_requires_auth(monkeypatch, tmp_path):
    _use_tmp_audit(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/alerts/telegram/status")
    assert response.status_code in (401, 403)


def test_templates_endpoint_requires_auth():
    with TestClient(app) as client:
        response = client.get("/api/alerts/templates")
    assert response.status_code in (401, 403)


def test_test_send_locked_records_audit_entry(monkeypatch, tmp_path):
    """A locked test-send attempt via the endpoint writes an audit entry (auth mocked)."""
    _use_tmp_audit(monkeypatch, tmp_path)
    for key in ["ENABLE_TELEGRAM_TEST_SEND", "ENABLE_TELEGRAM_SEND",
                "TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"]:
        monkeypatch.delenv(key, raising=False)

    from backend.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "tester"}
    try:
        with TestClient(app) as client:
            response = client.post("/api/alerts/telegram/test-send")
        assert response.status_code == 200
        data = response.json()
        assert data["sent"] is False
        assert data["network_call_made"] is False
        assert data["gate_status"] == "locked"
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    entries = read_recent_attempts()
    assert len(entries) == 1
    assert entries[0]["kind"] == "test_send"
    assert entries[0]["outcome"] == "locked"


def test_telegram_status_endpoint_no_secret_leak(monkeypatch, tmp_path):
    """Status endpoint must never include token/chat/authorized-id values."""
    _use_tmp_audit(monkeypatch, tmp_path)
    secret_token = "FAKE_TOKEN_VALUE_FOR_LEAK_TEST_ONLY"
    secret_chat = "556677889900"
    secret_ids = "121212121,343434343"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", secret_token)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", secret_chat)
    monkeypatch.setenv("AUTHORIZED_USER_IDS", secret_ids)

    from backend.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "tester"}
    try:
        with TestClient(app) as client:
            response = client.get("/api/alerts/telegram/status")
        assert response.status_code == 200
        body = response.text
        assert secret_token not in body
        assert secret_chat not in body
        assert "121212121" not in body
        assert "343434343" not in body
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_templates_render_endpoint(monkeypatch):
    from backend.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "tester"}
    try:
        with TestClient(app) as client:
            listing = client.get("/api/alerts/templates")
            assert listing.status_code == 200
            assert len(listing.json()["templates"]) >= 5

            rendered = client.post("/api/alerts/templates/render", json={
                "template_id": "system_health",
                "params": {"status_line": "All systems nominal"},
            })
            assert rendered.status_code == 200
            assert "All systems nominal" in rendered.json()["rendered"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ── standing safety guarantees ───────────────────────────────────────────────

def test_default_state_still_safe(monkeypatch):
    for key in ["ENABLE_TELEGRAM_SEND", "ENABLE_TELEGRAM_TEST_SEND", "ENABLE_ALERT_SCHEDULER"]:
        monkeypatch.delenv(key, raising=False)
    with TestClient(app) as client:
        response = client.get("/api/system/safety-matrix")
    assert response.status_code == 200
    data = response.json()
    assert data["safety_state"] == "SAFE"
    assert data["can_run_test_send"] is False
    assert data["test_send_gate_status"] == "locked"


def test_dry_run_preview_records_attempt_and_never_sends(monkeypatch, tmp_path):
    _use_tmp_audit(monkeypatch, tmp_path)
    from backend.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "tester"}
    try:
        with TestClient(app) as client:
            response = client.post("/api/alerts/telegram/dry-run-preview", json={"ticker": "2222.SR"})
        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["would_send"] is False
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    entries = read_recent_attempts()
    assert len(entries) == 1
    assert entries[0]["kind"] == "dry_run"
    assert entries[0]["network_call_made"] is False
