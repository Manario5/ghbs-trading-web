"""
UAT live UI fixes — backend behavior tests.

Covers the backend-observable parts of the UAT fixes:
- Anthropic test endpoint response shape / gating (#1)
- Safety warning reasons are accurate and never mention scheduler when off (#4)
- SAFE/WARNING/UNSAFE terminology consistency between safety-matrix and
  live-preview-status (#5)
- Alias-aware Telegram integration status (#8)
- Scheduler readiness locked when ENABLE_ALERT_SCHEDULER=false (#6-related)
- No secret leaks in the touched endpoints
"""
import os
import subprocess

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.safety_state import compute_safety_state

FROZEN_STRATEGY_FILES = [
    "tasi_engine_v7_2_1.py",
    "backend/core/classifier.py",
    "backend/core/regime.py",
    "backend/core/sizes.py",
    "backend/core/chandelier.py",
    "backend/core/executor.py",
    "backend/core/universe.py",
]

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _clear(monkeypatch):
    for key in [
        "ALLOW_PRODUCTION_DB", "DB_PATH", "PRODUCTION_DB_READONLY_REQUIRED",
        "ENABLE_LIVE_ANALYZE_PREVIEW", "ENABLE_LIVE_SCOUT_PREVIEW",
        "ENABLE_ALERT_SCHEDULER", "ENABLE_PROVIDER_COVERAGE_SCAN",
        "ENABLE_MARKET_DATA_SMOKE_TESTS", "ENABLE_TELEGRAM_SEND",
        "ENABLE_TELEGRAM_TEST_SEND", "ENABLE_API_SMOKE_TESTS",
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID",
        "WEBAPP_TELEGRAM_BOT_TOKEN", "WEBAPP_TELEGRAM_CHAT_ID",
        "ANTHROPIC_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)


def _auth():
    from backend.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "tester"}
    return get_current_user


# ── #4 warning reasons ───────────────────────────────────────────────────────

def test_warning_reasons_do_not_mention_scheduler_when_off(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "true")
    monkeypatch.setenv("DB_PATH", "tasi_ledger_test.db")
    with TestClient(app) as client:
        data = client.get("/api/system/safety-matrix").json()
    assert data["safety_state"] == "WARNING"
    assert data["mode_label"] == "LIVE-UAT"
    assert "Live Analyze Preview enabled" in data["warning_reasons"]
    joined = " ".join(data["warning_reasons"]).lower()
    assert "scheduler" not in joined


def test_warning_reasons_list_scheduler_only_when_on(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "true")
    monkeypatch.setenv("DB_PATH", "tasi_ledger_test.db")
    with TestClient(app) as client:
        data = client.get("/api/system/safety-matrix").json()
    assert data["safety_state"] == "WARNING"
    assert "Alert Scheduler enabled" in data["warning_reasons"]


def test_warning_reasons_multiple_gates(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("DB_PATH", "tasi_ledger_test.db")
    monkeypatch.setenv("ENABLE_PROVIDER_COVERAGE_SCAN", "true")
    monkeypatch.setenv("ENABLE_LIVE_SCOUT_PREVIEW", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "true")
    with TestClient(app) as client:
        data = client.get("/api/system/safety-matrix").json()
    reasons = data["warning_reasons"]
    assert "Provider coverage scan enabled" in reasons
    assert "Live Scout Preview enabled" in reasons
    assert "Telegram test-send enabled" in reasons
    assert "Alert Scheduler enabled" not in reasons


def test_default_safe_has_no_reasons(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("DB_PATH", "tasi_ledger_test.db")
    with TestClient(app) as client:
        data = client.get("/api/system/safety-matrix").json()
    assert data["safety_state"] == "SAFE"
    assert data["mode_label"] == "SAFE"
    assert data["warning_reasons"] == []
    assert data["unsafe_reasons"] == []


# ── #5 terminology consistency ───────────────────────────────────────────────

def test_matrix_and_preview_agree_in_live_uat(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("DB_PATH", "tasi_ledger_test.db")
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "true")
    with TestClient(app) as client:
        matrix = client.get("/api/system/safety-matrix").json()
        preview = client.get("/api/system/live-preview-status").json()
    assert matrix["safety_state"] == preview["safety_state"] == "WARNING"
    assert matrix["mode_label"] == preview["mode_label"] == "LIVE-UAT"


def test_unsafe_only_for_dangerous_conditions(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "true")
    monkeypatch.setenv("DB_PATH", "dangerous_prod.db")
    with TestClient(app) as client:
        data = client.get("/api/system/safety-matrix").json()
    assert data["safety_state"] == "UNSAFE"
    assert data["mode_label"] == "UNSAFE"
    assert len(data["unsafe_reasons"]) >= 1


def test_compute_safety_state_unit():
    # execution active => UNSAFE regardless of gates
    r = compute_safety_state("tasi_ledger_test.db", exec_active=True)
    assert r["safety_state"] == "UNSAFE"
    assert "Execution guard reported active execution capability" in r["unsafe_reasons"]


# ── #8 alias-aware Telegram integration status ───────────────────────────────

def test_integration_status_alias_aware_primary(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "FAKE_PRIMARY_TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/integrations/status").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    tg = data["telegram_alert_bot"]
    assert tg["configured"] is True
    assert tg["status_text"] == "Configured"
    assert tg["token_source"] == "TELEGRAM_BOT_TOKEN"


def test_integration_status_alias_aware_alias_only(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("TELEGRAM_TOKEN", "FAKE_ALIAS_TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/integrations/status").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    tg = data["telegram_alert_bot"]
    assert tg["configured"] is True
    assert tg["token_source"] == "TELEGRAM_TOKEN"


def test_integration_status_legacy_webapp_token(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("WEBAPP_TELEGRAM_BOT_TOKEN", "FAKE_LEGACY_TOKEN")
    monkeypatch.setenv("WEBAPP_TELEGRAM_CHAT_ID", "67890")
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/integrations/status").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    tg = data["telegram_alert_bot"]
    assert tg["configured"] is True
    assert tg["token_source"] == "WEBAPP_TELEGRAM_BOT_TOKEN"


def test_integration_status_not_configured(monkeypatch):
    _clear(monkeypatch)
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/integrations/status").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    assert data["telegram_alert_bot"]["configured"] is False
    assert data["telegram_alert_bot"]["token_source"] == "missing"


def test_integration_status_no_secret_leak(monkeypatch):
    _clear(monkeypatch)
    secret = "FAKE_SECRET_TOKEN_LEAKCHECK_123456789"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", secret)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "998877")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "FAKE_ANTHROPIC_LEAKCHECK")
    dep = _auth()
    try:
        with TestClient(app) as client:
            resp = client.get("/api/integrations/status")
    finally:
        app.dependency_overrides.pop(dep, None)
    assert secret not in resp.text
    assert "FAKE_ANTHROPIC_LEAKCHECK" not in resp.text


# ── #1 Anthropic test endpoint gating/shape ──────────────────────────────────

def test_anthropic_test_disabled_by_default(monkeypatch):
    _clear(monkeypatch)
    dep = _auth()
    try:
        with TestClient(app) as client:
            resp = client.post("/api/integrations/anthropic/test")
    finally:
        app.dependency_overrides.pop(dep, None)
    assert resp.status_code == 400
    assert "disabled" in resp.json()["detail"].lower()


def test_anthropic_test_missing_key(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("ENABLE_API_SMOKE_TESTS", "true")
    dep = _auth()
    try:
        with TestClient(app) as client:
            resp = client.post("/api/integrations/anthropic/test")
    finally:
        app.dependency_overrides.pop(dep, None)
    assert resp.status_code == 400
    assert "ANTHROPIC_API_KEY" in resp.json()["detail"]


# ── #6 scheduler readiness locked when flag false ────────────────────────────

def test_scheduler_readiness_locked_default(monkeypatch):
    _clear(monkeypatch)
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/scheduler/readiness").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    assert data["scheduler_enabled_in_env"] is False
    assert data["is_running"] is False
    assert data["gates"]["scheduled_send_gate_status"] == "locked"


def test_scheduler_status_reports_enabled_in_env_false(monkeypatch):
    _clear(monkeypatch)
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/scheduler/status").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    assert data["enabled_in_env"] is False
    assert data["is_running"] is False


# ── #11 frozen strategy files unchanged on this branch ───────────────────────

def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True
    )


def test_frozen_strategy_files_not_modified_on_branch():
    """The UAT branch must not touch any frozen strategy file vs origin/main."""
    if _git("rev-parse", "--git-dir").returncode != 0:
        pytest.skip("not a git checkout")

    base = _git("merge-base", "origin/main", "HEAD")
    if base.returncode != 0 or not base.stdout.strip():
        pytest.skip("origin/main baseline unavailable")

    diff = _git("diff", "--name-only", f"{base.stdout.strip()}..HEAD")
    if diff.returncode != 0:
        pytest.skip("git diff unavailable")

    changed = set(diff.stdout.split())
    offenders = [f for f in FROZEN_STRATEGY_FILES if f in changed]
    assert offenders == [], f"Frozen strategy files modified: {offenders}"


def test_frozen_strategy_files_exist():
    for rel in FROZEN_STRATEGY_FILES:
        assert os.path.exists(os.path.join(REPO_ROOT, rel)), f"missing {rel}"
