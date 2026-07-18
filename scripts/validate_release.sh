#!/bin/bash

echo "Validating Release Candidate..."

echo "1. Running backend tests..."
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi
export PYTHONPATH=$(pwd)
python3 -m pytest backend/tests -q
if [ $? -ne 0 ]; then
    echo "ERROR: Backend tests failed!"
    exit 1
fi

echo "2. Validating frontend build..."
npm run build
if [ $? -ne 0 ]; then
    echo "ERROR: Frontend build failed!"
    exit 1
fi

echo "3. Validating frontend types..."
npx tsc --noEmit
if [ $? -ne 0 ]; then
    echo "ERROR: Frontend type checks failed!"
    exit 1
fi

echo "4. Scanning for leaked secrets..."
bash scripts/secret_scan_extended.sh
if [ $? -ne 0 ]; then
    echo "ERROR: Secrets validation failed!"
    exit 1
fi

echo "5. Validating production DB gate negative checks..."
bash scripts/db_gate_negative_tests.sh
if [ $? -ne 0 ]; then
    echo "ERROR: DB gate negative tests failed!"
    exit 1
fi

echo "6. Validating live preview negative checks..."
bash scripts/live_preview_negative_tests.sh
if [ $? -ne 0 ]; then
    echo "ERROR: Live preview negative tests failed!"
    exit 1
fi

echo "7. Validating provider readiness negative checks..."
bash scripts/provider_negative_tests.sh
if [ $? -ne 0 ]; then
    echo "ERROR: Provider negative tests failed!"
    exit 1
fi

echo "8. Validating Telegram dry-run negative checks..."
./scripts/telegram_negative_tests.sh
echo "----------------------------------------"
echo "Release Candidate Validated Successfully!"
echo "----------------------------------------"
exit 0
