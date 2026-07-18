"""
File-based alert attempt audit layer — Release Train A.

Records every Telegram dry-run / test-send attempt (locked or allowed) as a
JSONL entry.  No DB migration framework exists, so this is append-only file
storage next to the runtime working directory.

Rules:
- Only masked/derived data is written — never token, chat ID, or user ID values.
- Reading returns the most recent entries first.
- Failures to write must never break the calling endpoint.
"""
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

AUDIT_FILE_ENV = "ALERT_AUDIT_FILE"
DEFAULT_AUDIT_FILE = "alert_attempts_audit.jsonl"

# Fields permitted in an audit entry — anything else is dropped.
_ALLOWED_FIELDS = {
    "timestamp",
    "kind",              # "dry_run" | "test_send"
    "outcome",           # "locked" | "sent" | "failed"
    "gate_status",
    "network_call_made",
    "blocked_reasons",
    "template_id",
    "target_chat_masked",
    "message_excerpt",   # first 80 chars of rendered message (templates only, no secrets)
}


def _audit_path() -> str:
    return os.environ.get(AUDIT_FILE_ENV, "").strip() or DEFAULT_AUDIT_FILE


def record_alert_attempt(entry: Dict[str, Any]) -> bool:
    """Append a sanitized audit entry. Returns True on success, False otherwise."""
    sanitized = {k: v for k, v in entry.items() if k in _ALLOWED_FIELDS}
    sanitized.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    try:
        with open(_audit_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(sanitized, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def read_recent_attempts(limit: int = 20) -> List[Dict[str, Any]]:
    """Return up to `limit` most recent audit entries, newest first."""
    path = _audit_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return []

    entries: List[Dict[str, Any]] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(entries) >= limit:
            break
    return entries


def last_attempt() -> Optional[Dict[str, Any]]:
    """Return the most recent attempt, or None."""
    recent = read_recent_attempts(limit=1)
    return recent[0] if recent else None
