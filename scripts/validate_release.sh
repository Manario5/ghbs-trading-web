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

echo "----------------------------------------"
echo "Release Candidate Validated Successfully!"
echo "----------------------------------------"
exit 0
