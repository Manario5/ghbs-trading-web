#!/bin/bash
set -euo pipefail

echo "Running extended secret scan..."

python3 - <<'PY'
from pathlib import Path
import re
import subprocess
import sys

REAL_ANTHROPIC = re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")
REAL_TELEGRAM = re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35,}\b")

SKIP_FILES = {
    "package-lock.json",
    "scripts/secret_scan.py",
    "scripts/secret_scan_extended.sh",
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico",
    ".woff", ".woff2", ".lock", ".db", ".sqlite",
    ".zip", ".tar", ".gz",
}

ALLOWLIST = [
    "TEST_TELEGRAM_TOKEN_NOT_REAL",
    "FAKE_TOKEN_VALUE_FOR_LEAK_TEST_ONLY",
    "SHOULD_NEVER_BE_WRITTEN",
    "sk-ant-supersecret-value-67890",
    "tok-supersecret-value-12345",
    "999999999:SECRETSECRETSECRETSECRETSECRETSECRET",
    "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
    "987654321:ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvu",
    "change_me_for_sandbox",
    "PASTE_YOUR",
]

SENSITIVE_ENV_KEYS = [
    "ANTHROPIC_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_TOKEN",
    "TELEGRAM_CHAT_ID",
    "AUTHORIZED_USER_IDS",
    "TWELVEDATA_API_KEY",
    "SAHMK_API_KEY",
    "TRADINGVIEW_API_KEY",
]

def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    for item in out.stdout.splitlines():
        path = Path(item)
        if item in SKIP_FILES:
            continue
        if path.suffix in SKIP_EXTENSIONS:
            continue
        yield item

def is_allowlisted(line: str) -> bool:
    return any(token in line for token in ALLOWLIST)

suspects = []

for file_path in tracked_files():
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            for idx, line in enumerate(fh, 1):
                if is_allowlisted(line):
                    continue
                if REAL_ANTHROPIC.search(line):
                    suspects.append((file_path, idx, "real-looking Anthropic key pattern"))
                if REAL_TELEGRAM.search(line):
                    suspects.append((file_path, idx, "real-looking Telegram bot token pattern"))
    except OSError:
        continue

env_example = Path(".env.example")
if env_example.exists():
    for idx, line in enumerate(env_example.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key in SENSITIVE_ENV_KEYS and value.strip():
            suspects.append((".env.example", idx, f"{key} must be blank"))

if suspects:
    for path, idx, reason in suspects:
        print(f"Suspected secret leak found in: {path}:{idx} ({reason})")
    sys.exit(1)

print("PASS: Extended secret scan found no real-looking leaked secrets.")
PY
