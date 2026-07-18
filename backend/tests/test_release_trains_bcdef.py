"""
Release Trains B–F tests.

B — validation infra sanity (secret scan importable, pytest config effective)
C — provider health: locked defaults, fallback reporting, no network by default
D — preview readiness: locked defaults, sample format, no engine execution
E — scheduler readiness: not running by default, scheduled sends locked,
    Telegram network blocked, audit of scheduled attempts
F — ops-status and deep health: aggregate visibility, no secret leaks
"""
import asyncio

from fastapi.testclient import TestClient

from backend.main import app
from backend.core.provider_health import get_provider_health
from backend.core.preview_readiness import get_preview_readiness, build_sample_preview
from backend.core.scheduler_readiness import (
    get_scheduler_readiness,
    evaluate_scheduled_send_gates,
    record_scheduled_attempt,
    SCHEDULED_JOB_DEFINITIONS,
)
from backend.core.alert_audit import read_recent_attempts, AUDIT_FILE_ENV


def _clear_gates(monkeypatch):
    for key in [
        "ENABLE_MARKET_DATA_SMOKE_TESTS", "ENABLE_PROVIDER_COVERAGE_SCAN",
        "ENABLE_LIVE_ANALYZE_PREVIEW", "ENABLE_LIVE_SCOUT_PREVIEW",
        "ENABLE_OHLCV_DIAGNOSTICS", "ENABLE_ALERT_SCHEDULER",
        "ENABLE_TELEGRAM_SEND", "ENABLE_TELEGRAM_TEST_SEND",
        "ALLOW_PRODUCTION_DB",
        "TWELVEDATA_API_KEY", "SAHMK_API_KEY", "TRADINGVIEW_API_KEY",
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID",
    ]:
        monkeypatch.delenv(key, raising=False)


def _auth_override():
    from backend.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "tester"}
    return get_current_user


# ── Train B ──────────────────────────────────────────────────────────────────

def test_secret_scan_script_runs_clean():
    import subprocess, sys
    result = subprocess.run([sys.executable, "scripts/secret_scan.py"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SECRET SCAN CLEAN" in result.stdout


async def test_async_tests_run_natively():
    """pytest.ini asyncio_mode=auto lets bare async tests execute (Train B)."""
    await asyncio.sleep(0)
    assert True


# ── Train C ──────────────────────────────────────────────────────────────────

def test_provider_health_locked_by_default(monkeypatch):
    _clear_gates(monkeypatch)
    health = get_provider_health()
    assert health["network_calls_locked"] is True
    assert health["safety_state"] == "SAFE"
    yf = next(p for p in health["providers"] if p["provider"] == "yfinance")
    assert yf["health"] == "locked"


def test_provider_fallback_reporting(monkeypatch):
    _clear_gates(monkeypatch)
    monkeypatch.setenv("TWELVEDATA_API_KEY", "FAKE_KEY_FOR_TEST")
    health = get_provider_health()
    assert health["effective_fallback_chain"] == ["yfinance", "twelvedata"]
    skipped = {s["provider"]: s["reason"] for s in health["skipped_providers"]}
    assert "sahmk" in skipped and "tradingview" in skipped
    assert "adapter not implemented" in skipped["sahmk"]


def test_provider_missing_key_reported(monkeypatch):
    _clear_gates(monkeypatch)
    health = get_provider_health()
    td = next(p for p in health["providers"] if p["provider"] == "twelvedata")
    assert td["health"] == "missing_key"
    assert td["secret_masked"] == "missing"


def test_provider_health_endpoint_no_key_leak(monkeypatch):
    _clear_gates(monkeypatch)
    fake_key = "FAKE_TWELVEDATA_KEY_VALUE_XYZ"
    monkeypatch.setenv("TWELVEDATA_API_KEY", fake_key)
    dep = _auth_override()
    try:
        with TestClient(app) as client:
            response = client.get("/api/market-data/provider-health")
        assert response.status_code == 200
        assert fake_key not in response.text
        assert response.json()["network_calls_locked"] is True
    finally:
        app.dependency_overrides.pop(dep, None)


def test_locked_smoke_test_makes_no_network_call(monkeypatch):
    """With gates off, the smoke-test service path returns an error before any fetch."""
    _clear_gates(monkeypatch)

    def _explode(*args, **kwargs):
        raise AssertionError("Network call attempted while gates locked")

    import backend.services.market_data_service as mds
    monkeypatch.setattr(mds, "yf", _explode, raising=False)

    from backend.services.market_data_service import MarketDataService
    service = MarketDataService()
    result = asyncio.run(service.test_universe_sample(limit=1))
    assert "error" in result
    result2 = asyncio.run(service.run_provider_coverage_scan(limit=1))
    assert "error" in result2


# ── Train D ──────────────────────────────────────────────────────────────────

def test_preview_readiness_locked_by_default(monkeypatch):
    _clear_gates(monkeypatch)
    readiness = get_preview_readiness()
    assert readiness["can_run_analyze_preview"] is False
    assert readiness["can_run_scout_preview"] is False
    assert readiness["safety_state"] == "SAFE"
    assert readiness["writes_production_db"] is False
    assert readiness["executes_trades"] is False
    assert "ENABLE_LIVE_ANALYZE_PREVIEW is false" in readiness["analyze_blockers"]


def test_preview_readiness_open_when_flags_set(monkeypatch):
    _clear_gates(monkeypatch)
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "true")
    monkeypatch.setenv("ENABLE_LIVE_SCOUT_PREVIEW", "true")
    monkeypatch.setenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "true")
    monkeypatch.setenv("ENABLE_OHLCV_DIAGNOSTICS", "true")
    monkeypatch.setenv("DB_PATH", "tasi_ledger_test.db")
    readiness = get_preview_readiness()
    assert readiness["can_run_analyze_preview"] is True
    assert readiness["can_run_scout_preview"] is True
    assert readiness["safety_state"] == "WARNING"


def test_preview_blocked_if_production_db(monkeypatch):
    _clear_gates(monkeypatch)
    monkeypatch.setenv("ENABLE_LIVE_ANALYZE_PREVIEW", "true")
    monkeypatch.setenv("ENABLE_MARKET_DATA_SMOKE_TESTS", "true")
    monkeypatch.setenv("ENABLE_OHLCV_DIAGNOSTICS", "true")
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "true")
    readiness = get_preview_readiness()
    assert readiness["can_run_analyze_preview"] is False
    assert any("ALLOW_PRODUCTION_DB" in b for b in readiness["safety_blockers"])


def test_sample_preview_is_static_and_marked():
    sample = build_sample_preview()
    assert sample["sample"] is True
    assert sample["dry_run"] is True
    assert "result_format" in sample
    assert sample["result_format"]["ticker"] == "0000.SR"


def test_live_analyze_endpoint_locked_by_default(monkeypatch):
    _clear_gates(monkeypatch)
    dep = _auth_override()
    try:
        with TestClient(app) as client:
            response = client.post("/api/live-preview/analyze/2222.SR")
        assert response.status_code == 400
        assert "disabled" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(dep, None)


def test_live_scout_endpoint_locked_by_default(monkeypatch):
    _clear_gates(monkeypatch)
    dep = _auth_override()
    try:
        with TestClient(app) as client:
            response = client.post("/api/live-preview/scout", json={})
        assert response.status_code == 400
    finally:
        app.dependency_overrides.pop(dep, None)


# ── Train E ──────────────────────────────────────────────────────────────────

def test_scheduler_not_running_by_default(monkeypatch):
    _clear_gates(monkeypatch)
    readiness = get_scheduler_readiness()
    assert readiness["scheduler_enabled_in_env"] is False
    assert readiness["jobs_running"] == 0
    assert readiness["auto_start_on_boot"] is False
    assert readiness["real_scheduled_sends_implemented"] is False
    assert readiness["safety_state"] == "SAFE"


def test_scheduled_send_gates_locked_by_default(monkeypatch):
    _clear_gates(monkeypatch)
    gates = evaluate_scheduled_send_gates()
    assert gates["can_run_scheduled_sends"] is False
    assert gates["scheduled_send_gate_status"] == "locked"
    assert "ENABLE_ALERT_SCHEDULER is false" in gates["blocked_reasons"]
    assert "ENABLE_TELEGRAM_SEND is false" in gates["blocked_reasons"]


def test_scheduled_sends_blocked_by_production_db(monkeypatch):
    _clear_gates(monkeypatch)
    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "FAKE_FOR_TEST")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setenv("ALLOW_PRODUCTION_DB", "true")
    gates = evaluate_scheduled_send_gates()
    assert gates["can_run_scheduled_sends"] is False
    assert "ALLOW_PRODUCTION_DB must be false" in gates["blocked_reasons"]


def test_manual_and_scheduled_sends_mutually_exclusive(monkeypatch):
    """No single .env can open both the manual test-send and scheduled-send gates."""
    from backend.core.telegram_sender import evaluate_test_send_gates
    _clear_gates(monkeypatch)
    monkeypatch.setenv("ENABLE_TELEGRAM_SEND", "true")
    monkeypatch.setenv("ENABLE_TELEGRAM_TEST_SEND", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "FAKE_FOR_TEST")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "false")
    assert evaluate_test_send_gates()["can_run_test_send"] is True
    assert evaluate_scheduled_send_gates()["can_run_scheduled_sends"] is False

    monkeypatch.setenv("ENABLE_ALERT_SCHEDULER", "true")
    assert evaluate_test_send_gates()["can_run_test_send"] is False
    assert evaluate_scheduled_send_gates()["can_run_scheduled_sends"] is True


def test_scheduled_attempt_audited(monkeypatch, tmp_path):
    monkeypatch.setenv(AUDIT_FILE_ENV, str(tmp_path / "audit.jsonl"))
    record_scheduled_attempt("daily_system_health", "locked", ["ENABLE_ALERT_SCHEDULER is false"])
    entries = read_recent_attempts()
    assert len(entries) == 1
    assert entries[0]["kind"] == "scheduled"
    assert entries[0]["outcome"] == "locked"
    assert entries[0]["network_call_made"] is False


def test_job_definitions_reference_known_templates():
    from backend.core.alert_templates import TEMPLATES
    for job in SCHEDULED_JOB_DEFINITIONS:
        assert job["template_id"] in TEMPLATES, f"{job['job_id']} references unknown template"


def test_scheduler_readiness_endpoint(monkeypatch):
    _clear_gates(monkeypatch)
    dep = _auth_override()
    try:
        with TestClient(app) as client:
            response = client.get("/api/scheduler/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is False
        assert data["gates"]["scheduled_send_gate_status"] == "locked"
        assert data["jobs_defined"] >= 3
    finally:
        app.dependency_overrides.pop(dep, None)


# ── Train F ──────────────────────────────────────────────────────────────────

def test_health_deep(monkeypatch):
    _clear_gates(monkeypatch)
    with TestClient(app) as client:
        response = client.get("/api/system/health-deep")
    assert response.status_code == 200
    data = response.json()
    assert data["db_connectivity"] is True
    assert data["safety_state"] == "SAFE"
    assert data["status"] == "ok"


def test_ops_status_aggregates_everything(monkeypatch):
    _clear_gates(monkeypatch)
    with TestClient(app) as client:
        response = client.get("/api/system/ops-status")
    assert response.status_code == 200
    data = response.json()
    for section in ["safety_matrix", "secrets_masked", "provider_health",
                    "preview_readiness", "scheduler_readiness", "telegram_readiness"]:
        assert section in data
    assert data["overall_state"] == "SAFE"


def test_ops_status_no_secret_leak(monkeypatch):
    _clear_gates(monkeypatch)
    fakes = {
        "TELEGRAM_BOT_TOKEN": "FAKE_TG_TOKEN_LEAKCHECK",
        "TELEGRAM_CHAT_ID": "998877665544",
        "ANTHROPIC_API_KEY": "FAKE_ANTHROPIC_LEAKCHECK",
        "TWELVEDATA_API_KEY": "FAKE_TWELVE_LEAKCHECK",
        "SAHMK_API_KEY": "FAKE_SAHMK_LEAKCHECK",
        "TRADINGVIEW_API_KEY": "FAKE_TV_LEAKCHECK",
        "AUTHORIZED_USER_IDS": "111000111,222000222",
    }
    for k, v in fakes.items():
        monkeypatch.setenv(k, v)
    with TestClient(app) as client:
        response = client.get("/api/system/ops-status")
    assert response.status_code == 200
    body = response.text
    for value in fakes.values():
        assert value not in body
    assert "111000111" not in body
