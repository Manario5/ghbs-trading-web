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
        "TELEGRAM_TOKEN",
        "TELEGRAM_CHAT_ID",
        "AUTHORIZED_USER_IDS",
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
check(status["telegram_token_source"] == "missing", "token source should be missing by default")
check(status["telegram_token_alias_configured"] is False, "alias should be missing by default")
check(status["telegram_token_alias_used"] is False, "alias should not be used by default")
check(status["authorized_user_ids_configured"] is False, "authorized ids should be missing by default")
check(status["authorized_user_ids_count"] == 0, "authorized ids count should be 0 by default")
check(status["telegram_dry_run_enabled"] is True, "dry-run should default true")
check(status["telegram_send_enabled"] is False, "send should default false")
check(status["telegram_test_send_enabled"] is False, "test send should default false")
check(status["can_send_telegram"] is False, "can_send_telegram must be false")
check(status["can_run_test_send"] is False, "can_run_test_send must be false")
check(status["telegram_network_calls_locked"] is True, "network calls must be locked")
check(status["safety_state"] == "SAFE", "default state must be SAFE")

fake_alias_token = "123456789:" + ("A" * 35)
fake_chat = "987654321"
fake_ids = "111,222,333"

os.environ["TELEGRAM_TOKEN"] = fake_alias_token
os.environ["TELEGRAM_CHAT_ID"] = fake_chat
os.environ["AUTHORIZED_USER_IDS"] = fake_ids
os.environ["ENABLE_TELEGRAM_SEND"] = "false"
os.environ["ENABLE_TELEGRAM_TEST_SEND"] = "false"
os.environ["ENABLE_ALERT_SCHEDULER"] = "false"

status = get_telegram_alert_status()
status_text = json.dumps(status)

check(status["telegram_bot_token_configured"] is True, "alias token should configure bot token")
check(status["telegram_bot_token_masked"] == "configured", "token should be masked configured")
check(status["telegram_chat_id_masked"] == "configured", "chat id should be masked configured")
check(status["telegram_token_source"] == "TELEGRAM_TOKEN", "alias token source should be TELEGRAM_TOKEN")
check(status["telegram_token_alias_configured"] is True, "alias should be configured")
check(status["telegram_token_alias_used"] is True, "alias should be used when primary missing")
check(status["authorized_user_ids_masked"] == "configured", "authorized ids should be masked configured")
check(status["authorized_user_ids_count"] == 3, "authorized ids count should be 3")
check(fake_alias_token not in status_text, "token leaked in status")
check(fake_chat not in status_text, "chat id leaked in status")
check("111" not in status_text and "222" not in status_text and "333" not in status_text, "authorized ids leaked in status")
check(status["can_send_telegram"] is False, "configured token must not allow send")

fake_primary_token = "123456789:" + ("B" * 35)
os.environ["TELEGRAM_BOT_TOKEN"] = fake_primary_token

status = get_telegram_alert_status()
status_text = json.dumps(status)

check(status["telegram_token_source"] == "TELEGRAM_BOT_TOKEN", "primary token should take precedence")
check(status["telegram_token_alias_configured"] is True, "alias can still be configured")
check(status["telegram_token_alias_used"] is False, "alias should not be used when primary exists")
check(fake_primary_token not in status_text, "primary token leaked in status")
check(fake_alias_token not in status_text, "alias token leaked in status")

preview = build_telegram_dry_run_preview({
    "ticker": "2222",
    "signal": "WATCH",
    "setup_type": "DRY_RUN_TEST",
})
preview_text = json.dumps(preview)

check(preview["dry_run"] is True, "preview must be dry-run")
check(preview["would_send"] is False, "preview must not send")
check(preview["execution_allowed"] is False, "execution must be false")
check(fake_primary_token not in preview_text, "primary token leaked in preview")
check(fake_alias_token not in preview_text, "alias token leaked in preview")
check(fake_chat not in preview_text, "chat id leaked in preview")

with TestClient(app) as client:
    response = client.get("/api/system/telegram-alert-status")
    check(response.status_code == 200, "status endpoint should return 200")
    check(fake_primary_token not in response.text, "primary token leaked from endpoint")
    check(fake_alias_token not in response.text, "alias token leaked from endpoint")
    check(fake_chat not in response.text, "chat id leaked from endpoint")
    check("111" not in response.text and "222" not in response.text and "333" not in response.text, "authorized ids leaked from endpoint")

    matrix = client.get("/api/system/safety-matrix")
    check(matrix.status_code == 200, "safety matrix should return 200")
    matrix_json = matrix.json()
    check(matrix_json["safety_state"] == "SAFE", "safety matrix should remain SAFE")
    check(matrix_json["telegram_network_calls_locked"] is True, "telegram network calls should be locked")

reset_env()
print("All Telegram negative checks passed.")
PY

echo "Telegram Negative Tests passed successfully."
