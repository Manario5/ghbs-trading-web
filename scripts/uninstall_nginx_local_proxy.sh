#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo"
  exit 1
fi

echo "Removing local Nginx sandbox proxy configurations..."

rm -f /etc/nginx/sites-enabled/ghbs-trading-local-sandbox.conf
rm -f /etc/nginx/sites-available/ghbs-trading-local-sandbox.conf

echo "Validating remaining Nginx configurations..."
if nginx -t >/dev/null 2>&1; then
    echo "Nginx configuration is valid. Reloading Nginx..."
    systemctl reload nginx
    echo "Local Nginx sandbox proxy successfully uninstalled cleanly."
else
    echo "WARNING: Nginx configuration validation failed!"
    echo "The remaining Nginx setup has syntax errors. You may need to manually inspect /etc/nginx."
fi
