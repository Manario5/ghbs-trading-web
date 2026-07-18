#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo"
  exit 1
fi

if ! command -v nginx >/dev/null 2>&1; then
    echo "Nginx is not installed. Nothing to uninstall."
    exit 0
fi

echo "Removing Nginx domain HTTP proxy configurations..."

rm -f /etc/nginx/sites-enabled/ghbs-trading-domain-http.conf
rm -f /etc/nginx/sites-available/ghbs-trading-domain-http.conf

echo "Validating remaining Nginx configurations..."
if nginx -t >/dev/null 2>&1; then
    echo "Nginx configuration is valid. Reloading Nginx..."
    systemctl reload nginx
    echo "Nginx domain proxy successfully uninstalled."
else
    echo "WARNING: Nginx configuration validation failed!"
    echo "The remaining Nginx setup has syntax errors. You may need to manually inspect /etc/nginx."
fi
