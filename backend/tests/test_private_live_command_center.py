"""
Private Live Command Center tests.

- Operating-mode derivation and labels (PRIVATE LIVE / AUTOMATED ALERTS /
  LOCKED-MAINTENANCE)
- Dashboard chart endpoints return safe empty states with no data
- Read-only guarantees: production DB write impossible, no execution
- Docs / live profile exist, .env.example defaults stay safe
- No secrets leaked in the new endpoints
"""
import os

from fastapi.testclient import TestClient

from backend.main import app
from backend.core.operating_mode import get_operating_mode

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _clear(monkeypatch):
    for key in [
        "ENABLE_MARKET_DATA_SMOKE_TESTS", "ENABLE_API_SMOKE_TESTS",
        "ENABLE_OHLCV_DIAGNOSTICS", "ENABLE_PROVIDER_COVERAGE_SCAN",
        "ENABLE_LIVE_ANALYZE_PREVIEW", "ENABLE_LIVE_SCOUT_PREVIEW",
        "ENABLE_ALERT_SCHEDULER", "ALERT_SCHEDULER_DRY_RUN_ONLY",
        "ENABLE_TELEGRAM_SEND", "ENABLE_TELEGRAM_TEST_SEND",
        "ALLOW_PRODUCTION_DB", "ANTHROPIC_API_KEY",
        "TWELVEDATA_API_KEY",
    ]:
        monkeypatch.delenv(key, raising=False)


def _auth():
    from backend.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "tester"}
    return get_current_user


# ── operating-mode derivation ────────────────────────────────────────────────

def test_locked_maintenance_by_default(monkeypatch):
    _clear(monkeypatch)
    mode = get_operating_mode("tasi_ledger_test.db", exec_active=False)
    assert mode["mode"] == "LOCKED_MAINTENANCE"
    assert mode["mode_label"] == "LOCKED / MAINTENANCE"
    assert mode["production_db_write_possible"] is False
    assert mode["trade_execution_possible"] is False


def test_private_live_when_live_gate_on(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "true")
    mode = get_operating_mode("tasi_ledger_test.db", exec_active=False)
    assert mode["mode"] == "PRIVATE_LIVE"
    assert mode["mode_label"] == "PRIVATE LIVE"
    assert mode["capabilities"]["live_analyze_preview"] is True
    assert mode["live_preview_read_only"] is True


def test_automated_alerts_when_scheduler_on(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "true")
    mode = get_operating_mode("tasi_ledger_test.db", exec_active=False)
    assert mode["mode"] == "AUTOMATED_ALERTS"
    assert mode["mode_label"] == "AUTOMATED ALERTS"
    assert mode["automation"]["scheduler_enabled"] is True
    # scheduler takes precedence over live-preview labels
    monkeypatch.setenv("ENABLE_LIVE_SCOUT_PREVIEW", "true")
    assert get_operating_mode("tasi_ledger_test.db", False)["mode"] == "AUTOMATED_ALERTS"


def test_restricted_when_execution_active(monkeypatch):
    _clear(monkeypatch)
    mode = get_operating_mode("tasi_ledger_test.db", exec_active=True)
    assert mode["mode"] == "RESTRICTED"
    assert mode["production_db_write_possible"] is False


def test_telegram_sending_active_flag(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "true")
    mode = get_operating_mode("tasi_ledger_test.db", exec_active=False)
    assert mode["telegram_sending_active"] is True
    assert mode["mode"] == "PRIVATE_LIVE"


def test_blocked_invariants_always_true(monkeypatch):
    _clear(monkeypatch)
    for env in [{}, {"ENABLE_LIVE_ANALYZE_PREVIEW": "true"}, {"ENABLE_ALERT_SCHEDULER": "true"}]:
        _clear(monkeypatch)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        mode = get_operating_mode("tasi_ledger_test.db", exec_active=False)
        assert mode["blocked"]["trade_execution"] is True
        assert mode["blocked"]["broker_execution"] is True
        assert mode["blocked"]["production_db_write"] is True
        assert mode["blocked"]["public_exposure"] is True


# ── operating-mode endpoint ──────────────────────────────────────────────────

def test_operating_mode_endpoint(monkeypatch):
    _clear(monkeypatch)
    with TestClient(app) as client:
        data = client.get("/api/system/operating-mode").json()
    assert data["mode"] == "LOCKED_MAINTENANCE"
    assert data["production_db_write_possible"] is False
    assert "generated_at" in data


def test_operating_mode_endpoint_no_secret_leak(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "FAKE_ANTHROPIC_LEAKCHECK_XYZ")
    monkeypatch.setenv("TWELVEDATA_API_KEY", "FAKE_TWELVE_LEAKCHECK_XYZ")
    with TestClient(app) as client:
        resp = client.get("/api/system/operating-mode")
    assert "FAKE_ANTHROPIC_LEAKCHECK_XYZ" not in resp.text
    assert "FAKE_TWELVE_LEAKCHECK_XYZ" not in resp.text


# ── dashboard chart endpoints (empty states, read-only) ──────────────────────

def test_dashboard_charts_empty_state(monkeypatch):
    _clear(monkeypatch)
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/dashboard/charts").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    # trade executions always present and always zero
    outcomes = {i["label"]: i["count"] for i in data["live_preview_outcomes"]["items"]}
    assert outcomes["Trade executions"] == 0
    assert data["regime_trend"]["available"] in (True, False)


def test_dashboard_scout_funnel_empty_state(monkeypatch):
    _clear(monkeypatch)
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/dashboard/scout-funnel").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    assert "available" in data and "stages" in data
    if not data["available"]:
        assert data["stages"] == []
        assert data["message"]


def test_dashboard_alert_activity_empty_state(monkeypatch):
    _clear(monkeypatch)
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/dashboard/alert-activity").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    assert "series" in data and "totals" in data


def test_dashboard_live_summary_readonly_guarantees(monkeypatch):
    _clear(monkeypatch)
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/dashboard/live-summary").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    assert data["production_db_write_possible"] is False
    assert data["trade_execution_possible"] is False
    assert data["live_preview_read_only"] is True
    assert "risk_snapshot" in data


def test_dashboard_provider_health_locked_default(monkeypatch):
    _clear(monkeypatch)
    dep = _auth()
    try:
        with TestClient(app) as client:
            data = client.get("/api/dashboard/provider-health").json()
    finally:
        app.dependency_overrides.pop(dep, None)
    assert data["network_calls_locked"] is True


def test_dashboard_endpoints_require_auth():
    with TestClient(app) as client:
        for path in ["/api/dashboard/charts", "/api/dashboard/scout-funnel",
                     "/api/dashboard/alert-activity", "/api/dashboard/live-summary",
                     "/api/dashboard/provider-health"]:
            assert client.get(path).status_code in (401, 403), path


# ── artifacts: docs, profile, safe defaults ──────────────────────────────────

def test_live_profile_and_docs_exist():
    for rel in [
        ".env.live.example",
        "docs/PRIVATE_LIVE_OPERATING_MODE.md",
        "docs/PRIVATE_LIVE_PROFILE.md",
        "docs/DASHBOARD_CHARTS.md",
        "docs/LIVE_OPERATIONS_RUNBOOK.md",
    ]:
        assert os.path.exists(os.path.join(REPO_ROOT, rel)), f"missing {rel}"


def test_env_example_defaults_safe():
    with open(os.path.join(REPO_ROOT, ".env.example"), encoding="utf-8") as f:
        content = f.read()
    for line in [
        "ALLOW_PRODUCTION_DB=false",
        "ENABLE_ALERT_SCHEDULER=false",
        "ENABLE_PROVIDER_COVERAGE_SCAN=false",
        "ENABLE_MARKET_DATA_SMOKE_TESTS=false",
        "ENABLE_LIVE_ANALYZE_PREVIEW=false",
        "ENABLE_LIVE_SCOUT_PREVIEW=false",
        "ENABLE_TELEGRAM_SEND=false",
        "ENABLE_TELEGRAM_TEST_SEND=false",
    ]:
        assert line in content, f"{line} not safe in .env.example"


def test_env_live_example_keeps_prod_db_locked():
    with open(os.path.join(REPO_ROOT, ".env.live.example"), encoding="utf-8") as f:
        content = f.read()
    assert "ALLOW_PRODUCTION_DB=false" in content
    assert "PRODUCTION_DB_READONLY_REQUIRED=true" in content
