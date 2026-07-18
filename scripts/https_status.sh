#!/bin/bash

DOMAIN=$1
if [ -z "$DOMAIN" ]; then
    echo "ERROR: Domain argument required."
    exit 1
fi

echo "================================================="
echo " GHBS HTTPS Status (Phase 6O) "
echo "================================================="

if systemctl is-active --quiet nginx; then
    echo "Nginx: RUNNING"
else
    echo "Nginx: INACTIVE"
fi

echo ""
echo "[Port Status]"
if command -v ss >/dev/null 2>&1; then
    ss -tlnp | grep -E ':80\s' || echo "Port 80 NOT listening via ss."
    ss -tlnp | grep -E ':443\s' || echo "Port 443 NOT listening via ss."
elif command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep -E ':80\s' || echo "Port 80 NOT listening via netstat."
    netstat -tlnp | grep -E ':443\s' || echo "Port 443 NOT listening via netstat."
fi

echo ""
echo "[Nginx Config]"
if nginx -t >/dev/null 2>&1; then
    echo "PASS: Nginx syntax is valid."
else
    echo "FAIL: Nginx syntax check failed."
fi

echo ""
echo "[HTTP/HTTPS Route Tests]"
HTTP_STATUS=$(curl -sw "%{http_code}" http://$DOMAIN/ -o /dev/null)
echo "HTTP Root: $HTTP_STATUS"

HTTPS_STATUS=$(curl -k -sw "%{http_code}" https://$DOMAIN/ -o /dev/null)
echo "HTTPS Root: $HTTPS_STATUS"

HTTPS_API_STATUS=$(curl -k -sw "%{http_code}" https://$DOMAIN/api/system/safety-matrix -o /dev/null)
echo "HTTPS API Safety Matrix: $HTTPS_API_STATUS"

if [ "$HTTPS_API_STATUS" == "200" ]; then
    echo "PASS: HTTPS API is reachable. Verifying Safety..."
    curl -k -s https://$DOMAIN/api/system/safety-matrix | grep -q '"safety_state":"SAFE"' && echo "Safety Matrix is SAFE." || echo "WARNING: Safety Matrix NOT SAFE."
else
    echo "WARNING: HTTPS API did not return 200."
fi

echo "================================================="
