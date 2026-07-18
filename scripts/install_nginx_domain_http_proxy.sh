#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo (e.g., sudo bash scripts/install_nginx_domain_http_proxy.sh example.com)"
  exit 1
fi

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo "ERROR: Domain argument is required."
    echo "Usage: sudo bash scripts/install_nginx_domain_http_proxy.sh example.com"
    exit 1
fi

# Reject localhost, IPs, and invalid domains
if [[ "$DOMAIN" == "localhost" ]] || [[ "$DOMAIN" == "127.0.0.1" ]] || [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || [[ "$DOMAIN" == *"/"* ]] || [[ "$DOMAIN" == *":"* ]] || [[ "$DOMAIN" == "http://"* ]] || [[ "$DOMAIN" == "https://"* ]]; then
    echo "ERROR: Invalid domain. Please provide a valid public domain name (e.g., example.com)."
    exit 1
fi

echo "Selected domain: $DOMAIN"

PROJECT_DIR=$(pwd)

# Verify Nginx is installed
if ! command -v nginx >/dev/null 2>&1; then
    echo "ERROR: Nginx is not installed."
    echo "To install Nginx on Ubuntu/Debian, run: sudo apt update && sudo apt install nginx"
    echo "Please install Nginx first, then run this script again."
    exit 1
fi

# Verify .env exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "ERROR: .env file is missing. Please run this script from the project root directory."
    exit 1
fi

echo "Verifying Sandbox Safety Context inside .env..."
grep -q "^ALLOW_PRODUCTION_DB=false" "$PROJECT_DIR/.env" || { echo "ERROR: ALLOW_PRODUCTION_DB must be false"; exit 1; }
grep -q "^DB_PATH=tasi_ledger_test.db" "$PROJECT_DIR/.env" || { echo "ERROR: DB_PATH must be tasi_ledger_test.db"; exit 1; }
grep -q "^ENABLE_ALERT_SCHEDULER=false" "$PROJECT_DIR/.env" || { echo "ERROR: ENABLE_ALERT_SCHEDULER must be false"; exit 1; }
grep -q "^ENABLE_PROVIDER_COVERAGE_SCAN=false" "$PROJECT_DIR/.env" || { echo "ERROR: ENABLE_PROVIDER_COVERAGE_SCAN must be false"; exit 1; }
grep -q "^ENABLE_LIVE_ANALYZE_PREVIEW=false" "$PROJECT_DIR/.env" || { echo "ERROR: ENABLE_LIVE_ANALYZE_PREVIEW must be false"; exit 1; }
grep -q "^ENABLE_LIVE_SCOUT_PREVIEW=false" "$PROJECT_DIR/.env" || { echo "ERROR: ENABLE_LIVE_SCOUT_PREVIEW must be false"; exit 1; }

echo "Verifying systemd services are active..."
if ! systemctl is-active --quiet ghbs-backend.service; then
    echo "ERROR: ghbs-backend.service is not active. Please start it before enabling the proxy."
    exit 1
fi
if ! systemctl is-active --quiet ghbs-frontend.service; then
    echo "ERROR: ghbs-frontend.service is not active. Please start it before enabling the proxy."
    exit 1
fi

echo "Verifying Safety Matrix..."
if ! sudo -u "$SUDO_USER" bash "$PROJECT_DIR/scripts/check_safety.sh"; then
    echo "ERROR: Safety check failed! System is not SAFE."
    exit 1
fi

echo "Installing Nginx domain HTTP proxy for $DOMAIN..."
sed "s|__DOMAIN__|$DOMAIN|g" "$PROJECT_DIR/deploy/nginx-ghbs-domain-http.conf.example" > /etc/nginx/sites-available/ghbs-trading-domain-http.conf

ln -sfn /etc/nginx/sites-available/ghbs-trading-domain-http.conf /etc/nginx/sites-enabled/ghbs-trading-domain-http.conf

echo "Validating Nginx configuration..."
if nginx -t; then
    echo "Nginx configuration is valid. Reloading Nginx..."
    systemctl reload nginx
    echo "Nginx domain proxy successfully installed and enabled for $DOMAIN on port 80."
else
    echo "ERROR: Nginx configuration validation failed!"
    echo "Removing invalid proxy file to prevent Nginx failure..."
    rm -f /etc/nginx/sites-enabled/ghbs-trading-domain-http.conf
    rm -f /etc/nginx/sites-available/ghbs-trading-domain-http.conf
    exit 1
fi
