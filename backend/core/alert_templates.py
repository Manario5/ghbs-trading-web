"""
Alert template registry — Release Train A.

Single source of truth for test-message and future system-alert templates.
Templates contain no secrets and render with sanitized string parameters only.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

TEMPLATES: Dict[str, Dict[str, str]] = {
    # ── test templates ──
    "general_test": {
        "title": "General Test Alert",
        "category": "test",
        "body": "GHBS TASI Sandbox: General system check. Pipeline is nominal.",
    },
    "manual_test_send": {
        "title": "Manual Test-Send",
        "category": "test",
        "body": "GHBS TASI — Manual Test-Send\nTime (UTC): {timestamp}\nMode: MANUAL TEST ONLY",
    },
    "scout_summary_test": {
        "title": "Scout Summary Test",
        "category": "test",
        "body": "GHBS TASI Sandbox Scout: Found {count} candidate setups (R/R > 2.0). Review command center for details.",
    },
    # ── future system alert templates (locked; delivery not implemented) ──
    "setup_detected": {
        "title": "Setup Detected",
        "category": "system",
        "body": "GHBS TASI Alert\nTicker: {ticker}\nSignal: {signal}\nSetup: {setup_type}\nRegime: {regime}",
    },
    "tp_hit": {
        "title": "Target Profit Hit",
        "category": "system",
        "body": "GHBS TASI Alert: TP hit on {ticker}. Level: {level}.",
    },
    "stop_hit": {
        "title": "Stop Condition Met",
        "category": "system",
        "body": "GHBS TASI Alert: Stop condition met on {ticker}. Chandelier level: {level}.",
    },
    "system_health": {
        "title": "System Health",
        "category": "system",
        "body": "GHBS TASI System: {status_line}",
    },
}


def list_templates() -> List[Dict[str, str]]:
    """Return template metadata (id, title, category, body) — safe to expose via API."""
    return [
        {"id": tid, "title": t["title"], "category": t["category"], "body": t["body"]}
        for tid, t in TEMPLATES.items()
    ]


def render_template(template_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Render a template with the given params.

    Unknown template ids and missing/extra params never raise — missing keys
    are left as literal placeholders so previews stay predictable.
    """
    params = dict(params or {})
    params.setdefault("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    template = TEMPLATES.get(template_id)
    if template is None:
        return {
            "template_id": template_id,
            "known_template": False,
            "rendered": "",
            "error": "Unknown template id",
        }

    class _SafeDict(dict):
        def __missing__(self, key):  # leave unresolved placeholders visible
            return "{" + key + "}"

    rendered = template["body"].format_map(_SafeDict(**{k: str(v) for k, v in params.items()}))
    return {
        "template_id": template_id,
        "known_template": True,
        "title": template["title"],
        "category": template["category"],
        "rendered": rendered,
    }
