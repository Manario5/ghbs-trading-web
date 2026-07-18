#!/bin/bash
set -euo pipefail

echo "Running Telegram Negative Tests..."

python3 - <<'PY'
import json
import os
import sys
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.telegram_readiness import (
    get_telegram_alert_status,
    build_telegram_dry_run_preview,
)


def reset_env():
    for key in [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "ENABLE_TELEGRAM_DRY_RUN",
        "ENABLE_TELEGRAM_SEND",
        "ENABLE_TELEGRAM_TEST_SEND",
        "ENABLE_ALERT_SCHEDULER",
    ]:
        os.environ.pop(key, None)


def check(condition, message):
    if not condition:
        print(f"FAILED: {message}")
        sys.exit(1)


reset_env()
status = get_telegram_alert_status()

check(status["telegram_bot_token_configured"] is False, "token should be missing by default")
check(status["telegram_chat_id_configured"] is False, "chat id should be missing by default")
check(status["telegram_dry_run_enabled"] is True, "dry-run should default true")
check(status["telegram_send_enabled"] is False, "send should default false")
check(status["telegram_test_send_enabled"] is False, "test send should default false")
check(status["can_send_telegram"] is False, "can_send_telegram must be false")
check(status["can_run_test_send"] is False, "can_run_test_send must be false")
check(status["telegram_network_calls_locked"] is True, "network calls must be locked")
check(status["safety_state"] == "SAFE", "default state must be SAFE")

fake_token = "123456789:" + ("A" * 35)
fake_chat = "987654321"

os.environ["TELEGRAM_BOT_TOKEN"] = fake_token
os.environ["TELEGRAM_CHAT_ID"] = fake_chat
os.environ["ENABLE_TELEGRAM_SEND"] = "false"
os.environ["ENABLE_TELEGRAM_TEST_SEND"] = "false"
os.environ["ENABLE_ALERT_SCHEDULER"] = "false"

status = get_telegram_alert_status()
status_text = json.dumps(status)

check(status["telegram_bot_token_masked"] == "configured", "token should be masked configured")
check(status["telegram_chat_id_masked"] == "configured", "chat id should be masked configured")
check(fake_token not in status_text, "token leaked in status")
check(fake_chat not in status_text, "chat id leaked in status")
check(status["can_send_telegram"] is False, "configured token must not allow send")

preview = build_telegram_dry_run_preview({
    "ticker": "2222",
    "signal": "WATCH",
    "setup_type": "DRY_RUN_TEST",
})
preview_text = json.dumps(preview)

check(preview["dry_run"] is True, "preview must be dry-run")
check(preview["would_send"] is False, "preview must not send")
check(preview["execution_allowed"] is False, "execution must be false")
check(fake_token not in preview_text, "token leaked in preview")
check(fake_chat not in preview_text, "chat id leaked in preview")

with TestClient(app) as client:
    response = client.get("/api/system/telegram-alert-status")
    check(response.status_code == 200, "status endpoint should return 200")
    check(fake_token not in response.text, "token leaked from endpoint")
    check(fake_chat not in response.text, "chat id leaked from endpoint")

    matrix = client.get("/api/system/safety-matrix")
    check(matrix.status_code == 200, "safety matrix should return 200")
    matrix_json = matrix.json()
    check(matrix_json["safety_state"] == "SAFE", "safety matrix should remain SAFE")
    check(matrix_json["telegram_network_calls_locked"] is True, "telegram network calls should be locked")

reset_env()
print("All Telegram negative checks passed.")
PY

echo "Telegram Negative Tests passed successfully."
