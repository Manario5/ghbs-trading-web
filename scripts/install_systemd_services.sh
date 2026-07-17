#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo (e.g., sudo bash scripts/install_systemd_services.sh)"
  exit 1
fi

PROJECT_DIR=$(pwd)

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

echo "Sandbox safety constraints verified logically."

echo "Installing systemd services..."
cp "$PROJECT_DIR/deploy/ghbs-backend.service.example" /etc/systemd/system/ghbs-backend.service
cp "$PROJECT_DIR/deploy/ghbs-frontend.service.example" /etc/systemd/system/ghbs-frontend.service

# Inject dynamic paths mapping to the local project location securely
sed -i "s|/opt/ghbs-trading|$PROJECT_DIR|g" /etc/systemd/system/ghbs-backend.service
sed -i "s|/opt/ghbs-trading|$PROJECT_DIR|g" /etc/systemd/system/ghbs-frontend.service
# Remove any User bindings in case of conflicting system configurations as we explicitly run dynamically, alternatively can be updated to specific user. We leave it as is or replace with the $USER if root is invoking. For safety we can remove User=ghbs and rely on root/default or specifically dynamically map to $SUDO_USER
if [ -n "$SUDO_USER" ]; then
    sed -i "s|^User=ghbs|User=$SUDO_USER|g" /etc/systemd/system/ghbs-backend.service
    sed -i "s|^User=ghbs|User=$SUDO_USER|g" /etc/systemd/system/ghbs-frontend.service
else
    sed -i "/^User=ghbs/d" /etc/systemd/system/ghbs-backend.service
    sed -i "/^User=ghbs/d" /etc/systemd/system/ghbs-frontend.service
fi

systemctl daemon-reload
systemctl enable ghbs-backend.service ghbs-frontend.service

echo "Services mapped and enabled locally safely."

if [ "$1" == "--start" ]; then
    echo "Starting services natively..."
    systemctl start ghbs-backend.service ghbs-frontend.service
    echo "Services running natively. Check scripts/release_status.sh or scripts/systemd_status.sh limits."
else
    echo "Success! Services installed. To start them, use the --start flag or run:"
    echo "sudo systemctl start ghbs-backend ghbs-frontend"
fi
