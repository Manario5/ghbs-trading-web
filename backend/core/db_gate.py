import os
import sqlite3
from typing import Dict, Any


KNOWN_LEGACY_TABLES = [
    "positions",
    "transactions",
    "signal_events",
    "system_state",
    "setup_log",
]


def _env_bool(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def get_db_gate_status() -> Dict[str, Any]:
    allow_prod = _env_bool("ALLOW_PRODUCTION_DB", "false")
    db_path = os.environ.get("DB_PATH", "tasi_ledger_test.db").strip()
    prod_db_path = os.environ.get("PRODUCTION_DB_PATH", "").strip()
    gate_enabled = _env_bool("ENABLE_PRODUCTION_DB_READONLY_GATE", "false")
    readonly_required = _env_bool("PRODUCTION_DB_READONLY_REQUIRED", "true")

    db_path_sandbox_ok = db_path == "tasi_ledger_test.db"
    production_db_path_configured = bool(prod_db_path)
    prod_db_basename = os.path.basename(prod_db_path) if prod_db_path else ""

    gate_locked = not (
        allow_prod
        and gate_enabled
        and readonly_required
        and production_db_path_configured
        and db_path_sandbox_ok
    )

    error_category = "LOCKED" if gate_locked else "NONE"

    if not readonly_required:
        error_category = "UNSAFE_READONLY_NOT_REQUIRED"
    elif not db_path_sandbox_ok:
        error_category = "UNSAFE_DB_PATH_NOT_SANDBOX"
    elif gate_locked:
        error_category = "LOCKED"

    result: Dict[str, Any] = {
        "gate_enabled": gate_enabled,
        "gate_locked": gate_locked,
        "readonly_required": readonly_required,
        "production_db_path_configured": production_db_path_configured,
        "production_db_basename": prod_db_basename,
        "db_path_sandbox_ok": db_path_sandbox_ok,
        "can_attempt_readonly_connection": not gate_locked,
        "readonly_connection_ok": False,
        "detected_tables_count": 0,
        "detected_known_legacy_tables": [],
        "error_category": error_category,
    }

    if gate_locked:
        return result

    if not os.path.exists(prod_db_path):
        result["error_category"] = "FILE_NOT_FOUND"
        return result

    conn = None
    try:
        uri = f"file:{prod_db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        cursor = conn.cursor()

        cursor.execute("PRAGMA query_only=ON;")
        cursor.execute("SELECT sqlite_version();")
        cursor.execute("PRAGMA database_list;")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        tables = [row[0] for row in cursor.fetchall()]
        detected_legacy = [t for t in tables if t in KNOWN_LEGACY_TABLES]

        result["readonly_connection_ok"] = True
        result["detected_tables_count"] = len(tables)
        result["detected_known_legacy_tables"] = detected_legacy
        result["error_category"] = "NONE"

    except sqlite3.Error:
        result["error_category"] = "SQLITE_ERROR"
    except Exception:
        result["error_category"] = "CONNECTION_ERROR"
    finally:
        if conn is not None:
            conn.close()

    return result
