#!/bin/bash

DOMAIN=$1
EMAIL=$2
EXPECTED_IP=$3

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "ERROR: Usage: ./scripts/real_domain_deploy_precheck.sh DOMAIN EMAIL [EXPECTED_IP]"
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

PROJECT_DIR=$(pwd)
FAILED=0

echo "================================================="
echo " GHBS Real Domain Deploy Precheck (Phase 6P) "
echo "================================================="

# Check .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "FAIL: .env file is missing."
    FAILED=1
else
    # Verify sandbox constraints
    grep -q "^ALLOW_PRODUCTION_DB=false" "$PROJECT_DIR/.env" || { echo "FAIL: ALLOW_PRODUCTION_DB != false"; FAILED=1; }
    grep -q "^DB_PATH=tasi_ledger_test.db" "$PROJECT_DIR/.env" || { echo "FAIL: DB_PATH != tasi_ledger_test.db"; FAILED=1; }
    grep -q "^ENABLE_ALERT_SCHEDULER=false" "$PROJECT_DIR/.env" || { echo "FAIL: ENABLE_ALERT_SCHEDULER != false"; FAILED=1; }
    grep -q "^ENABLE_PROVIDER_COVERAGE_SCAN=false" "$PROJECT_DIR/.env" || { echo "FAIL: ENABLE_PROVIDER_COVERAGE_SCAN != false"; FAILED=1; }
    grep -q "^ENABLE_LIVE_ANALYZE_PREVIEW=false" "$PROJECT_DIR/.env" || { echo "FAIL: ENABLE_LIVE_ANALYZE_PREVIEW != false"; FAILED=1; }
    grep -q "^ENABLE_LIVE_SCOUT_PREVIEW=false" "$PROJECT_DIR/.env" || { echo "FAIL: ENABLE_LIVE_SCOUT_PREVIEW != false"; FAILED=1; }
    
    if grep -q "^ALLOW_PRODUCTION_DB=false" "$PROJECT_DIR/.env"; then
        echo "PASS: Sandbox .env configuration safely verified."
    fi
fi

# Verify Nginx
if ! systemctl is-active --quiet nginx; then
    echo "FAIL: Nginx is not running or not installed."
    FAILED=1
else
    echo "PASS: Nginx is active."
fi

# Verify Certbot
if ! command -v certbot >/dev/null 2>&1; then
    echo "WARNING: Certbot is not installed."
    echo "         To install: sudo apt update && sudo apt install certbot python3-certbot-nginx"
else
    echo "PASS: Certbot is installed."
fi

# Verify scripts
SCRIPTS_TO_CHECK=(
    "scripts/install_systemd_services.sh"
    "scripts/install_nginx_domain_http_proxy.sh"
    "scripts/check_domain_dns.sh"
    "scripts/certbot_https_preflight.sh"
    "scripts/install_certbot_https.sh"
    "scripts/https_status.sh"
)
for script in "${SCRIPTS_TO_CHECK[@]}"; do
    if [ ! -f "$PROJECT_DIR/$script" ]; then
        echo "FAIL: Required script $script is missing."
        FAILED=1
    else
        echo "PASS: Script $script exists."
    fi
done

# DNS Checks
echo "Running DNS validation..."
bash "$PROJECT_DIR/scripts/check_domain_dns.sh" "$DOMAIN" "$EXPECTED_IP" || FAILED=1

if [ $FAILED -ne 0 ]; then
    echo "================================================="
    echo " PRECHECK FAILED: Fix the above errors before proceeding."
    echo "================================================="
    exit 1
fi

echo "================================================="
echo " PRECHECK PASSED. System is ready for stack build."
echo "================================================="
exit 0
