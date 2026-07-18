"""
Provider health & fallback reporting — Release Train C.

Config-only evaluation: this module NEVER makes network calls. It reports,
per provider, whether the provider could serve requests if the gates were
opened, and what the effective fallback chain would be.

Providers:
- yfinance     — no key required
- twelvedata   — TWELVEDATA_API_KEY
- sahmk        — SAHMK_API_KEY (readiness only; fetch adapter not yet implemented)
- tradingview  — TRADINGVIEW_API_KEY (readiness only; fetch adapter not yet implemented)
"""
import os
from typing import Any, Dict, List

FALLBACK_ORDER = ["yfinance", "twelvedata", "sahmk", "tradingview"]

# Providers with an implemented fetch adapter in market_data_service.
IMPLEMENTED_PROVIDERS = {"yfinance", "twelvedata"}


def _env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def _configured(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def _gates_open() -> bool:
    return (
        _env_bool("ENABLE_MARKET_DATA_SMOKE_TESTS")
        or _env_bool("ENABLE_PROVIDER_COVERAGE_SCAN")
        or _env_bool("ENABLE_LIVE_ANALYZE_PREVIEW")
        or _env_bool("ENABLE_LIVE_SCOUT_PREVIEW")
    )


def provider_entry(name: str) -> Dict[str, Any]:
    key_env = {
        "yfinance": None,
        "twelvedata": "TWELVEDATA_API_KEY",
        "sahmk": "SAHMK_API_KEY",
        "tradingview": "TRADINGVIEW_API_KEY",
    }[name]

    key_ok = True if key_env is None else _configured(key_env)
    implemented = name in IMPLEMENTED_PROVIDERS
    usable_if_unlocked = key_ok and implemented

    if not implemented:
        health = "readiness_only"
    elif not key_ok:
        health = "missing_key"
    elif not _gates_open():
        health = "locked"
    else:
        health = "ready"

    return {
        "provider": name,
        "requires_secret": key_env is not None,
        "secret_env": key_env,
        "secret_masked": ("not required" if key_env is None
                          else ("configured" if key_ok else "missing")),
        "adapter_implemented": implemented,
        "usable_if_unlocked": usable_if_unlocked,
        "health": health,
    }


def get_provider_health() -> Dict[str, Any]:
    entries = [provider_entry(p) for p in FALLBACK_ORDER]
    effective_chain: List[str] = [e["provider"] for e in entries if e["usable_if_unlocked"]]
    skipped = [
        {"provider": e["provider"],
         "reason": ("adapter not implemented" if not e["adapter_implemented"]
                    else "API key missing")}
        for e in entries if not e["usable_if_unlocked"]
    ]

    gates_open = _gates_open()
    return {
        "configured_fallback_order": FALLBACK_ORDER,
        "effective_fallback_chain": effective_chain,
        "skipped_providers": skipped,
        "providers": entries,
        "network_calls_locked": not gates_open,
        "gates": {
            "market_data_smoke_tests_enabled": _env_bool("ENABLE_MARKET_DATA_SMOKE_TESTS"),
            "provider_coverage_scan_enabled": _env_bool("ENABLE_PROVIDER_COVERAGE_SCAN"),
            "live_analyze_preview_enabled": _env_bool("ENABLE_LIVE_ANALYZE_PREVIEW"),
            "live_scout_preview_enabled": _env_bool("ENABLE_LIVE_SCOUT_PREVIEW"),
        },
        "safety_state": "SAFE" if not gates_open else "WARNING",
    }
