#!/bin/bash

DOMAIN=$1
EXPECTED_IP=$2

if [ -z "$DOMAIN" ]; then
    echo "ERROR: Domain argument required."
    exit 1
fi

PROJECT_DIR=$(pwd)
FAILED=0

# Verify Nginx
if ! systemctl is-active --quiet nginx; then
    echo "FAIL: Nginx is not active."
    FAILED=1
else
    echo "PASS: Nginx is active."
fi

# Verify .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "FAIL: .env file missing in $PROJECT_DIR"
    FAILED=1
else
    grep -q "^ALLOW_PRODUCTION_DB=false" "$PROJECT_DIR/.env" || { echo "FAIL: ALLOW_PRODUCTION_DB != false"; FAILED=1; }
    grep -q "^DB_PATH=tasi_ledger_test.db" "$PROJECT_DIR/.env" || { echo "FAIL: DB_PATH != tasi_ledger_test.db"; FAILED=1; }
    grep -q "^ENABLE_ALERT_SCHEDULER=false" "$PROJECT_DIR/.env" || { echo "FAIL: ENABLE_ALERT_SCHEDULER != false"; FAILED=1; }
    echo "PASS: Sandbox .env check."
fi

# Verify systemd services
if ! systemctl is-active --quiet ghbs-backend.service; then echo "FAIL: Backend service inactive"; FAILED=1; else echo "PASS: Backend active"; fi
if ! systemctl is-active --quiet ghbs-frontend.service; then echo "FAIL: Frontend service inactive"; FAILED=1; else echo "PASS: Frontend active"; fi

# Verify Safety Matrix locally
if ! bash "$PROJECT_DIR/scripts/check_safety.sh"; then
    echo "FAIL: Safety Matrix local check failed."
    FAILED=1
else
    echo "PASS: Safety Matrix local check."
fi

# Verify Nginx config
CONFIG_FILE="/etc/nginx/sites-enabled/ghbs-trading-domain-http.conf"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "FAIL: HTTP proxy config $CONFIG_FILE not found."
    FAILED=1
fi
if ! nginx -t >/dev/null 2>&1; then
    echo "FAIL: nginx -t syntax check failed."
    FAILED=1
else
    echo "PASS: Nginx syntax."
fi

# Verify frontend route via domain
if curl -sw "%{http_code}" http://$DOMAIN/ -o /dev/null | grep -q '200'; then
    echo "PASS: Frontend via domain (HTTP 200)"
else
    echo "FAIL: Frontend via domain did not return 200"
    FAILED=1
fi

# Verify API via domain
if curl -sw "%{http_code}" http://$DOMAIN/api/system/safety-matrix -o /dev/null | grep -q '200'; then
    echo "PASS: Backend API via domain (HTTP 200)"
else
    echo "FAIL: Backend API via domain did not return 200"
    FAILED=1
fi

# Verify DNS
if ! bash "$PROJECT_DIR/scripts/check_domain_dns.sh" "$DOMAIN" "$EXPECTED_IP"; then
    echo "FAIL: DNS check failed."
    FAILED=1
fi

if [ $FAILED -ne 0 ]; then
    echo "=================================="
    echo " PREFLIGHT FAILED. DO NOT INSTALL "
    echo "=================================="
    exit 1
fi

echo "=================================="
echo " PREFLIGHT PASSED. READY FOR SSL  "
echo "=================================="
exit 0
