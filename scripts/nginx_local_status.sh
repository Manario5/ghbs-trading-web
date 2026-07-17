#!/bin/bash

echo "================================================="
echo " GHBS Nginx Local Proxy Status (Sandbox Phase 6M) "
echo "================================================="

echo ""
echo "[Nginx Installation Status]"
if command -v nginx >/dev/null 2>&1; then
    echo "Nginx is installed."
else
    echo "Nginx is NOT installed."
fi

echo ""
echo "[Nginx Execution Status]"
if systemctl is-active --quiet nginx; then
    echo "Nginx service is RUNNING."
else
    echo "Nginx service is STOPPED / INACTIVE."
fi

echo ""
echo "[Port 8080 Listening Status]"
if command -v ss >/dev/null 2>&1; then
    ss -tlnp | grep ':8080 ' || echo "Port 8080 NOT actively listening via ss."
elif command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep ':8080 ' || echo "Port 8080 NOT actively listening via netstat."
else
    echo "ss/netstat network utilities aren't strictly available to inspect local ports quickly."
fi

echo ""
echo "[Frontend HTTP Test]"
FRONTEND_HTTP_STATUS=$(curl -sw "%{http_code}" http://127.0.0.1:8080/ -o /dev/null)
if [ "$FRONTEND_HTTP_STATUS" == "200" ]; then
    echo "PASS: Frontend Route via 8080 (HTTP $FRONTEND_HTTP_STATUS)"
else
    echo "FAIL/WARNING: Frontend Route via 8080 (HTTP $FRONTEND_HTTP_STATUS)"
fi

echo ""
echo "[Backend Safety Matrix HTTP Test]"
BACKEND_HTTP_STATUS=$(curl -sw "%{http_code}" http://127.0.0.1:8080/api/system/safety-matrix -o /dev/null)
if [ "$BACKEND_HTTP_STATUS" == "200" ]; then
    echo "PASS: Backend API via 8080 (HTTP $BACKEND_HTTP_STATUS)"
else
    echo "FAIL/WARNING: Backend API via 8080 (HTTP $BACKEND_HTTP_STATUS)"
fi

echo "================================================="
