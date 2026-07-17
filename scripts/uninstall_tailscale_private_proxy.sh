#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo"
  exit 1
fi

echo "Removing Tailscale Private Nginx configurations securely natively..."

rm -f /etc/nginx/sites-enabled/ghbs-trading-tailscale-private.conf
rm -f /etc/nginx/sites-available/ghbs-trading-tailscale-private.conf

echo "Validating remaining Nginx boundaries..."
if nginx -t >/dev/null 2>&1; then
    echo "Nginx natively intact cleanly. Reloading intelligently..."
    systemctl reload nginx
    echo "Tailscale private proxy successfully responsibly uninstalled."
else
    echo "WARNING: Nginx natively reports syntax issues independently."
fi
exit 0
