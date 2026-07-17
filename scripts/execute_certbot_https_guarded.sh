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
    echo "ERROR: Usage: sudo bash scripts/execute_certbot_https_guarded.sh DOMAIN EMAIL [EXPECTED_IP]"
    exit 1
fi

if [[ "$DOMAIN" == "localhost" ]] || [[ "$DOMAIN" == "127.0.0.1" ]] || [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || [[ "$DOMAIN" == *"/"* ]] || [[ "$DOMAIN" == *":"* ]] || [[ "$DOMAIN" == "http://"* ]] || [[ "$DOMAIN" == "https://"* ]] || [[ "$DOMAIN" == "example.com" ]]; then
    echo "ERROR: Invalid domain: $DOMAIN"
    exit 1
fi

if [[ "$EMAIL" != *"@"* ]] || [[ "$EMAIL" != *"."* ]]; then
    echo "ERROR: Invalid email address: $EMAIL"
    exit 1
fi

# Verify Certbot
if ! command -v certbot >/dev/null 2>&1; then
    echo "ERROR: Certbot is not installed."
    echo "To install Certbot, run: sudo apt update && sudo apt install certbot python3-certbot-nginx"
    exit 1
fi

PROJECT_DIR=$(pwd)

echo "Running Preflight validations for Certbot bindings natively..."
if ! sudo -u "$SUDO_USER" bash "$PROJECT_DIR/scripts/certbot_https_preflight.sh" "$DOMAIN" "$EXPECTED_IP"; then
    echo "ERROR: Preflight bounds failed! Certbot execution aborted securely."
    exit 1
fi

echo ""
echo "=========================================================================="
echo " WARNING: You are about to map production SSL via Let's Encrypt Certbot.  "
echo " This natively modifies /etc/nginx boundaries dynamically securely.       "
echo "=========================================================================="
echo "Type exactly the following to proceed:"
echo "I_UNDERSTAND_RUN_CERTBOT_FOR_THIS_DOMAIN"
echo ""

read -p "> " USER_CONFIRMATION

if [ "$USER_CONFIRMATION" != "I_UNDERSTAND_RUN_CERTBOT_FOR_THIS_DOMAIN" ]; then
    echo "Confirmation did not match exactly explicitly. Aborted."
    exit 1
fi

echo "Confirmation securely verified intelligently. Executing Certbot wrapper smoothly..."

bash "$PROJECT_DIR/scripts/install_certbot_https.sh" "$DOMAIN" "$EMAIL" "$EXPECTED_IP"
CERT_EXIT=$?

if [ $CERT_EXIT -eq 0 ]; then
    echo "--------------------------------------------------------"
    echo " Let's Encrypt SSL Installation Successfully Processed! "
    echo "--------------------------------------------------------"
    echo "Post-Installation Status Check and Safety Validations:"
    echo "1. Run: bash scripts/https_status.sh $DOMAIN"
    echo "2. Run: curl -k -s https://$DOMAIN/api/system/safety-matrix"
else
    echo "Certbot installation explicitly failed safely natively."
    exit 1
fi
exit 0
