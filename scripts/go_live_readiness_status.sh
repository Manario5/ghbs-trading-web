#!/bin/bash

DOMAIN=$1

echo "=========================================================="
echo " GHBS GO-LIVE Readiness Status (Phase 6P) "
echo "=========================================================="

# Nginx
if systemctl is-active --quiet nginx; then
    echo "Nginx: RUNNING"
else
    echo "Nginx: STOPPED/INACTIVE"
fi

# Certbot
if command -v certbot >/dev/null 2>&1; then
    echo "Certbot: INSTALLED"
else
    echo "Certbot: NOT INSTALLED"
fi

# Systemd GHBS
if systemctl is-active --quiet ghbs-backend.service; then
    echo "Backend (systemd): RUNNING"
else
    echo "Backend (systemd): INACTIVE"
fi

if systemctl is-active --quiet ghbs-frontend.service; then
    echo "Frontend (systemd): RUNNING"
else
    echo "Frontend (systemd): INACTIVE"
fi

echo ""
echo "[Port Status]"
if command -v ss >/dev/null 2>&1; then
    ss -tlnp | grep -E ':80\s|:443\s' || echo "Ports 80/443 not explicitly listening."
fi

echo ""
echo "[Sandbox Environmental Constraints]"
PROJECT_DIR=$(pwd)
if [ -f "$PROJECT_DIR/.env" ]; then
    grep -q "^ALLOW_PRODUCTION_DB=false" "$PROJECT_DIR/.env" && echo "ALLOW_PRODUCTION_DB: false" || echo "ALLOW_PRODUCTION_DB: INVALID / MISSING"
    grep -q "^ENABLE_ALERT_SCHEDULER=false" "$PROJECT_DIR/.env" && echo "ENABLE_ALERT_SCHEDULER: false" || echo "ENABLE_ALERT_SCHEDULER: INVALID"
    grep -q "^ENABLE_PROVIDER_COVERAGE_SCAN=false" "$PROJECT_DIR/.env" && echo "ENABLE_PROVIDER_COVERAGE_SCAN: false" || echo "ENABLE_PROVIDER_COVERAGE_SCAN: INVALID"
    grep -q "^ENABLE_LIVE_ANALYZE_PREVIEW=false" "$PROJECT_DIR/.env" && echo "ENABLE_LIVE_ANALYZE_PREVIEW: false" || echo "ENABLE_LIVE_ANALYZE_PREVIEW: INVALID"
    grep -q "^ENABLE_LIVE_SCOUT_PREVIEW=false" "$PROJECT_DIR/.env" && echo "ENABLE_LIVE_SCOUT_PREVIEW: false" || echo "ENABLE_LIVE_SCOUT_PREVIEW: INVALID"
else
    echo "ERROR: .env File not found."
fi

if [ -n "$DOMAIN" ]; then
    echo ""
    echo "[HTTP Routes via $DOMAIN]"
    curl -sw "%{http_code}" http://$DOMAIN/ -o /dev/null | grep -q '200' && echo "HTTP Frontend: PASS" || echo "HTTP Frontend: FAIL"
    curl -sw "%{http_code}" http://$DOMAIN/api/system/safety-matrix -o /dev/null | grep -q '200' && echo "HTTP Safety Matrix: PASS" || echo "HTTP Safety Matrix: FAIL"

    echo ""
    echo "[HTTPS Routes via $DOMAIN]"
    curl -k -sw "%{http_code}" https://$DOMAIN/ -o /dev/null | grep -q '200' && echo "HTTPS Frontend: PASS" || echo "HTTPS Frontend: FAIL"
    
    HTTPS_SAFETY_HTTP=$(curl -k -sw "%{http_code}" https://$DOMAIN/api/system/safety-matrix -o /dev/null)
    if [ "$HTTPS_SAFETY_HTTP" == "200" ]; then
        curl -k -s https://$DOMAIN/api/system/safety-matrix | grep -q '"safety_state":"SAFE"' && echo "HTTPS Safety Matrix: PASS (SAFE)" || echo "HTTPS Safety Matrix: WARNING (NOT SAFE)"
    else
        echo "HTTPS Safety Matrix: FAIL (HTTP $HTTPS_SAFETY_HTTP)"
    fi
else
    echo ""
    echo "NOTICE: Specify a DOMAIN argument to validate external routes actively (e.g. bash scripts/go_live_readiness_status.sh DOMAIN)"
fi

echo "=========================================================="
