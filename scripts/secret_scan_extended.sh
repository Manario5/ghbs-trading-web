#!/bin/bash
set -euo pipefail

echo "Running extended secret scan..."

python3 - <<'PY'
from pathlib import Path
import re
import sys

ROOT = Path(".").resolve()

EXCLUDED_DIRS = {
    "node_modules", "venv", ".venv", "dist", ".git",
    "backups", ".pytest_cache", "__pycache__",
}

EXCLUDED_FILES = {"secret_scan_extended.sh"}

EXCLUDED_EXTENSIONS = {
    ".zip", ".gz", ".tar", ".tgz", ".pyc",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
    ".pdf", ".xlsx", ".docx",
    ".db", ".sqlite", ".sqlite3",
}

REAL_ANTHROPIC = re.compile(r"sk-ant-api[0-9A-Za-z_\-]{10,}")
REAL_TELEGRAM = re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35,}\b")

ENV_EXAMPLE_ALLOWED_KEYS = {
    "ANTHROPIC_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "TWELVEDATA_API_KEY",
    "SAHMK_API_KEY",
    "TRADINGVIEW_API_KEY",
    "PRODUCTION_DB_PATH",
    "ENABLE_PRODUCTION_DB_READONLY_GATE",
    "PRODUCTION_DB_READONLY_REQUIRED",
}

SAFE_PLACEHOLDERS = {
    "",
    "your_key_here",
    "your_token_here",
    "your_chat_id_here",
    "configured_for_status_only",
    "false",
    "true",
}

def is_excluded(path: Path) -> bool:
    if set(path.parts) & EXCLUDED_DIRS:
        return True
    if path.name in EXCLUDED_FILES:
        return True
    if path.suffix.lower() in EXCLUDED_EXTENSIONS:
        return True
    return False

suspects = []

for path in ROOT.rglob("*"):
    if not path.is_file() or is_excluded(path):
        continue

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    rel = path.relative_to(ROOT)

    for idx, line in enumerate(text.splitlines(), start=1):
        if REAL_ANTHROPIC.search(line):
            suspects.append((str(rel), idx, "real-looking Anthropic key pattern"))
        if REAL_TELEGRAM.search(line):
            suspects.append((str(rel), idx, "real-looking Telegram bot token pattern"))

env_example = ROOT / ".env.example"
if env_example.exists():
    for idx, line in enumerate(env_example.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in ENV_EXAMPLE_ALLOWED_KEYS and value.lower() not in SAFE_PLACEHOLDERS:
            suspects.append((".env.example", idx, f"{key} must be blank or safe placeholder only"))

if suspects:
    for file_path, line_no, reason in suspects:
        print(f"Suspected secret leak found in: {file_path}:{line_no} ({reason})")
    sys.exit(1)

print("PASS: Extended secret scan found no real-looking leaked secrets.")
PY
