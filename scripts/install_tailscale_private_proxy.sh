#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo"
  exit 1
fi

PROJECT_DIR=$(pwd)

# Verify Nginx
if ! command -v nginx >/dev/null 2>&1; then
    echo "ERROR: Nginx is not installed."
    exit 1
fi
if ! systemctl is-active --quiet nginx; then
    echo "ERROR: Nginx service is not active."
    exit 1
fi

# Verify Tailscale
if ! command -v tailscale >/dev/null 2>&1; then
    echo "ERROR: Tailscale is not installed."
    echo "Please install it officially: curl -fsSL https://tailscale.com/install.sh | sh"
    exit 1
fi

TAILSCALE_IP=$(tailscale ip -4 2>/dev/null)
if [ -z "$TAILSCALE_IP" ]; then
    echo "ERROR: Tailscale IP not found. Ensure tailscale is running (sudo tailscale up)."
    exit 1
fi

echo "Detected Private Tailscale IP: $TAILSCALE_IP"

# Verify .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "ERROR: .env file is missing. Please run from project root."
    exit 1
fi

echo "Verifying Sandbox Safety Context inside .env..."
grep -q "^ALLOW_PRODUCTION_DB=false" "$PROJECT_DIR/.env" || { echo "ERROR: ALLOW_PRODUCTION_DB != false"; exit 1; }
grep -q "^DB_PATH=tasi_ledger_test.db" "$PROJECT_DIR/.env" || { echo "ERROR: DB_PATH != tasi_ledger_test.db"; exit 1; }
grep -q "^ENABLE_ALERT_SCHEDULER=false" "$PROJECT_DIR/.env" || { echo "ERROR: ENABLE_ALERT_SCHEDULER != false"; exit 1; }
grep -q "^ENABLE_PROVIDER_COVERAGE_SCAN=false" "$PROJECT_DIR/.env" || { echo "ERROR: ENABLE_PROVIDER_COVERAGE_SCAN != false"; exit 1; }
grep -q "^ENABLE_LIVE_ANALYZE_PREVIEW=false" "$PROJECT_DIR/.env" || { echo "ERROR: ENABLE_LIVE_ANALYZE_PREVIEW != false"; exit 1; }
grep -q "^ENABLE_LIVE_SCOUT_PREVIEW=false" "$PROJECT_DIR/.env" || { echo "ERROR: ENABLE_LIVE_SCOUT_PREVIEW != false"; exit 1; }

echo "Verifying systemd services are active..."
if ! systemctl is-active --quiet ghbs-backend.service; then
    echo "ERROR: ghbs-backend.service is not active."
    exit 1
fi
if ! systemctl is-active --quiet ghbs-frontend.service; then
    echo "ERROR: ghbs-frontend.service is not active."
    exit 1
fi

echo "Verifying Safety Matrix natively..."
if [ -n "$SUDO_USER" ]; then
    SAFETY_CMD=(sudo -u "$SUDO_USER" bash "$PROJECT_DIR/scripts/check_safety.sh")
else
    SAFETY_CMD=(bash "$PROJECT_DIR/scripts/check_safety.sh")
fi

if ! "${SAFETY_CMD[@]}"; then
    echo "ERROR: Safety check failed! System is not SAFE."
    exit 1
fi

echo "Installing Tailscale Private Nginx proxy..."
sed "s|__TAILSCALE_IP__|$TAILSCALE_IP|g" "$PROJECT_DIR/deploy/nginx-ghbs-tailscale-private.conf.example" > /etc/nginx/sites-available/ghbs-trading-tailscale-private.conf

ln -sfn /etc/nginx/sites-available/ghbs-trading-tailscale-private.conf /etc/nginx/sites-enabled/ghbs-trading-tailscale-private.conf

echo "Validating Nginx configuration..."
if nginx -t; then
    echo "Nginx configuration strictly valid. Reloading Nginx natively..."
    systemctl reload nginx
    echo "Tailscale private proxy installed and actively bound exclusively on $TAILSCALE_IP:8080."
else
    echo "ERROR: Nginx configuration broken dynamically. Rolling back explicitly..."
    rm -f /etc/nginx/sites-enabled/ghbs-trading-tailscale-private.conf
    rm -f /etc/nginx/sites-available/ghbs-trading-tailscale-private.conf
    exit 1
fi
exit 0
