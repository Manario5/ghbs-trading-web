#!/usr/bin/env bash
# GHBS Trading web — full validation pipeline (Release Train B).
# Runs: backend tests, negative safety tests, frontend build, secret scan.
# Exits non-zero on the first failure. Safe to run anywhere; makes no network
# calls and never sends alerts (all gates stay at their process-env defaults).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== 1/4 Backend tests (full suite) ==="
python -m pytest backend/tests/ -q

echo "=== 2/4 Negative safety tests (explicit re-run) ==="
python -m pytest \
  backend/tests/test_secrets.py \
  backend/tests/test_phase6z.py \
  backend/tests/test_phase7a.py \
  backend/tests/test_release_train_a.py \
  backend/tests/test_release_trains_bcdef.py \
  backend/tests/test_uat_live_ui_fixes.py \
  backend/tests/test_private_live_command_center.py \
  -q

echo "=== 3/4 Frontend build ==="
npm run build --silent

echo "=== 4/4 Secret scan ==="
python scripts/secret_scan.py

echo ""
echo "FULL VALIDATION PASSED"
