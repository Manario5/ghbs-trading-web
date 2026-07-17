#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo"
  exit 1
fi

DOMAIN=$1
EMAIL=$2
EXPECTED_IP=$3

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "ERROR: Usage: sudo bash scripts/install_certbot_https.sh DOMAIN EMAIL [EXPECTED_IP]"
    exit 1
fi

# basic validation
if [[ "$DOMAIN" == "localhost" ]] || [[ "$DOMAIN" == "127.0.0.1" ]] || [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || [[ "$DOMAIN" == *"/"* ]] || [[ "$DOMAIN" == *":"* ]] || [[ "$DOMAIN" == "http://"* ]] || [[ "$DOMAIN" == "https://"* ]] || [[ "$DOMAIN" == "example.com" ]]; then
    echo "ERROR: Invalid domain: $DOMAIN"
    exit 1
fi

if [[ "$EMAIL" != *"@"* ]] || [[ "$EMAIL" != *"."* ]]; then
    echo "ERROR: Invalid email: $EMAIL"
    exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
    echo "ERROR: Certbot is not installed."
    echo "To install Certbot, run: sudo apt update && sudo apt install certbot python3-certbot-nginx"
    echo "Abort."
    exit 1
fi

PROJECT_DIR=$(pwd)
echo "Running Preflight checks..."
if ! sudo -u "$SUDO_USER" bash "$PROJECT_DIR/scripts/certbot_https_preflight.sh" "$DOMAIN" "$EXPECTED_IP"; then
    echo "ERROR: Preflight failed. Aborting Certbot installation."
    exit 1
fi

echo "Preflight passed. Executing Certbot..."
certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email

if [ $? -eq 0 ]; then
    echo "Certbot installation successful!"
    echo "Post-install verification commands:"
    echo "   bash scripts/https_status.sh $DOMAIN"
    echo "   curl https://$DOMAIN/api/system/safety-matrix"
else
    echo "Certbot installation failed!"
    exit 1
fi
exit 0
