import os
import pytest
from backend.core.provider_readiness import get_provider_readiness_status

def test_provider_readiness_default_locked():
    os.environ.clear()
    data = get_provider_readiness_status()
    assert data["provider_calls_locked"] is True
    assert data["can_run_provider_smoke_tests"] is False
    assert data["can_run_provider_coverage_scan"] is False
    assert data["safety_state"] == "SAFE"

def test_missing_secrets_masked():
    os.environ.clear()
    data = get_provider_readiness_status()
    assert data["providers"]["twelvedata"]["configured"] is False
    assert data["providers"]["twelvedata"]["secret_masked"] == "missing"
    assert data["providers"]["sahmk"]["configured"] is False
    assert data["providers"]["tradingview"]["configured"] is False

def test_configured_secrets_masked():
    os.environ.clear()
    os.environ["TWELVEDATA_API_KEY"] = "super-secret"
    os.environ["TRADINGVIEW_API_KEY"] = "another-secret"
    data = get_provider_readiness_status()
    
    assert data["providers"]["twelvedata"]["configured"] is True
    assert data["providers"]["twelvedata"]["secret_masked"] == "configured"
    assert "super-secret" not in str(data)
    
    assert data["providers"]["tradingview"]["configured"] is True
    assert data["providers"]["tradingview"]["secret_masked"] == "configured"
    assert "another-secret" not in str(data)

def test_smoke_tests_enabled():
    os.environ.clear()
    os.environ["ENABLE_MARKET_DATA_SMOKE_TESTS"] = "true"
    data = get_provider_readiness_status()
    assert data["provider_calls_locked"] is False
    assert data["can_run_provider_smoke_tests"] is True
    assert data["safety_state"] == "WARNING"

def test_coverage_scan_enabled():
    os.environ.clear()
    os.environ["ENABLE_PROVIDER_COVERAGE_SCAN"] = "true"
    data = get_provider_readiness_status()
    assert data["provider_calls_locked"] is False
    assert data["can_run_provider_coverage_scan"] is True
    assert data["safety_state"] == "UNSAFE"
