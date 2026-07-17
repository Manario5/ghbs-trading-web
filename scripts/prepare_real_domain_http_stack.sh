#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo (e.g., sudo bash scripts/prepare_real_domain_http_stack.sh DOMAIN [EXPECTED_IP])"
  exit 1
fi

DOMAIN=$1
EXPECTED_IP=$2

if [ -z "$DOMAIN" ]; then
    echo "ERROR: Usage: sudo bash scripts/prepare_real_domain_http_stack.sh DOMAIN [EXPECTED_IP]"
    exit 1
fi

if [[ "$DOMAIN" == "localhost" ]] || [[ "$DOMAIN" == "127.0.0.1" ]] || [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || [[ "$DOMAIN" == *"/"* ]] || [[ "$DOMAIN" == *":"* ]] || [[ "$DOMAIN" == "http://"* ]] || [[ "$DOMAIN" == "https://"* ]] || [[ "$DOMAIN" == "example.com" ]]; then
    echo "ERROR: Invalid domain: $DOMAIN"
    exit 1
fi

PROJECT_DIR=$(pwd)

# Safety .env checks
grep -q "^ALLOW_PRODUCTION_DB=false" "$PROJECT_DIR/.env" || { echo "ERROR: ALLOW_PRODUCTION_DB must be false"; exit 1; }
grep -q "^DB_PATH=tasi_ledger_test.db" "$PROJECT_DIR/.env" || { echo "ERROR: DB_PATH must be tasi_ledger_test.db"; exit 1; }
grep -q "^ENABLE_ALERT_SCHEDULER=false" "$PROJECT_DIR/.env" || { echo "ERROR: ENABLE_ALERT_SCHEDULER must be false"; exit 1; }

# Verify Nginx
if ! systemctl is-active --quiet nginx; then
    echo "ERROR: Nginx is not active. Please start Nginx before proceeding."
    exit 1
fi

echo "Verifying test database integrity safely..."
if [ -f "$PROJECT_DIR/tasi_ledger_test.db" ] && command -v sqlite3 >/dev/null 2>&1; then
    if ! sqlite3 "$PROJECT_DIR/tasi_ledger_test.db" "PRAGMA integrity_check;" | grep -q "ok"; then
        echo "WARNING: Test DB structural anomaly detected. Automatically renaming to isolate cleanly."
        mv "$PROJECT_DIR/tasi_ledger_test.db" "$PROJECT_DIR/tasi_ledger_test.db.corrupted_$(date +%s)"
    fi
fi

# Ensure Systemd is active
echo "Installing/starting GHBS Systemd Sandbox services..."
sudo bash "$PROJECT_DIR/scripts/install_systemd_services.sh" --start

sleep 2

if ! systemctl is-active --quiet ghbs-backend.service; then
    echo "ERROR: Backend failed to start natively."
    exit 1
fi

if ! systemctl is-active --quiet ghbs-frontend.service; then
    echo "ERROR: Frontend failed to start natively."
    exit 1
fi

echo "Verifying internal Sandbox Safety bounds cleanly..."
if ! sudo -u "$SUDO_USER" bash "$PROJECT_DIR/scripts/check_safety.sh"; then
    echo "ERROR: Sandbox Matrix structurally unsafe! Check logs."
    exit 1
fi

echo "Installing Nginx Domain HTTP proxy securely..."
sudo bash "$PROJECT_DIR/scripts/install_nginx_domain_http_proxy.sh" "$DOMAIN"

if ! nginx -t >/dev/null 2>&1; then
    echo "ERROR: Nginx configuration broken dynamically. Rolling back Proxy."
    rm -f /etc/nginx/sites-enabled/ghbs-trading-domain-http.conf
    rm -f /etc/nginx/sites-available/ghbs-trading-domain-http.conf
    systemctl reload nginx
    exit 1
fi

echo "=================================="
echo " Proxy Tests against $DOMAIN ..."
echo "=================================="

FRONTEND_HTTP_STATUS=$(curl -sw "%{http_code}" http://$DOMAIN/ -o /dev/null)
if [ "$FRONTEND_HTTP_STATUS" != "200" ]; then
    echo "FAIL: Frontend HTTP $FRONTEND_HTTP_STATUS"
    exit 1
fi

BACKEND_HTTP_STATUS=$(curl -sw "%{http_code}" http://$DOMAIN/api/system/safety-matrix -o /dev/null)
if [ "$BACKEND_HTTP_STATUS" != "200" ]; then
    echo "FAIL: Backend API HTTP $BACKEND_HTTP_STATUS"
    exit 1
fi

if ! curl -s "http://$DOMAIN/api/system/safety-matrix" | grep -q '"safety_state":"SAFE"'; then
    echo "FAIL: Safety Matrix is NOT SAFE through Nginx proxy!"
    exit 1
fi

if [ -n "$EXPECTED_IP" ]; then
    bash "$PROJECT_DIR/scripts/check_domain_dns.sh" "$DOMAIN" "$EXPECTED_IP"
fi

echo "STACK PREPARED SUCCESSFULLY (Sandbox Mode + Domain Proxy Active)."
exit 0
