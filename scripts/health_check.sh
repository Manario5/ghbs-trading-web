#!/bin/bash

echo "Running Health Check..."
FAILED=0

# Check Backend
echo -n "Checking backend (/api/system/safety-matrix)... "
BACKEND_STATUS=$(curl -sw "%{http_code}" http://127.0.0.1:8000/api/system/safety-matrix -o /dev/null)

if [ "$BACKEND_STATUS" == "200" ]; then
    echo "PASS"
else
    echo "FAIL (HTTP $BACKEND_STATUS)"
    FAILED=1
fi

# Check Frontend
echo -n "Checking frontend root (/).... "
FRONTEND_STATUS=$(curl -sw "%{http_code}" http://127.0.0.1:3000/ -o /dev/null)

if [ "$FRONTEND_STATUS" == "200" ]; then
    echo "PASS"
else
    echo "FAIL (HTTP $FRONTEND_STATUS)"
    FAILED=1
fi

if [ $FAILED -ne 0 ]; then
    echo "Health Check FAILED."
    exit 1
fi

echo "Health Check PASSED."
exit 0
