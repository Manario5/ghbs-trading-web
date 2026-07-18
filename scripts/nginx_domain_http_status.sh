#!/bin/bash

DOMAIN=$1

echo "=========================================================="
echo " GHBS Nginx Domain HTTP Proxy Status (Sandbox Phase 6N)   "
echo "=========================================================="

echo ""
echo "[Nginx Installation Status]"
if command -v nginx >/dev/null 2>&1; then
    echo "Nginx is installed."
else
    echo "Nginx is NOT installed."
fi

echo ""
echo "[Nginx Execution Status]"
if systemctl is-active --quiet nginx; then
    echo "Nginx service is RUNNING."
else
    echo "Nginx service is STOPPED / INACTIVE."
fi

echo ""
echo "[Port 80 Listening Status]"
if command -v ss >/dev/null 2>&1; then
    ss -tlnp | grep -E ':80\s' || echo "Port 80 NOT actively listening via ss."
elif command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep -E ':80\s' || echo "Port 80 NOT actively listening via netstat."
else
    echo "ss/netstat network utilities aren't strictly available."
fi

echo ""
echo "[Nginx Config Status]"
CONFIG_FILE="/etc/nginx/sites-enabled/ghbs-trading-domain-http.conf"
if [ -f "$CONFIG_FILE" ]; then
    echo "Config file is present: $CONFIG_FILE"
    CONFIGURED_DOMAIN=$(grep "server_name" "$CONFIG_FILE" | awk '{print $2}' | tr -d ';')
    echo "Configured domain: $CONFIGURED_DOMAIN"
else
    echo "Config file NOT found: $CONFIG_FILE"
    CONFIGURED_DOMAIN=""
fi

echo ""
echo "[HTTP Tests]"
if [ -n "$DOMAIN" ]; then
    echo "Testing using provided domain argument: $DOMAIN"
    
    FRONTEND_HTTP_STATUS=$(curl -sw "%{http_code}" http://$DOMAIN/ -o /dev/null)
    if [ "$FRONTEND_HTTP_STATUS" == "200" ]; then
        echo "PASS: Frontend Route via $DOMAIN (HTTP $FRONTEND_HTTP_STATUS)"
    else
        echo "FAIL/WARNING: Frontend Route via $DOMAIN (HTTP $FRONTEND_HTTP_STATUS)"
    fi

    BACKEND_HTTP_STATUS=$(curl -sw "%{http_code}" http://$DOMAIN/api/system/safety-matrix -o /dev/null)
    if [ "$BACKEND_HTTP_STATUS" == "200" ]; then
        echo "PASS: Backend API via $DOMAIN (HTTP $BACKEND_HTTP_STATUS)"
    else
        echo "FAIL/WARNING: Backend API via $DOMAIN (HTTP $BACKEND_HTTP_STATUS)"
    fi
else
    if [ -n "$CONFIGURED_DOMAIN" ]; then
        echo "No domain provided. Testing localhost with Host header: $CONFIGURED_DOMAIN"
        FRONTEND_HTTP_STATUS=$(curl -sw "%{http_code}" -H "Host: $CONFIGURED_DOMAIN" http://127.0.0.1/ -o /dev/null)
        if [ "$FRONTEND_HTTP_STATUS" == "200" ]; then
            echo "PASS: Frontend Route (HTTP $FRONTEND_HTTP_STATUS)"
        else
            echo "FAIL/WARNING: Frontend Route (HTTP $FRONTEND_HTTP_STATUS)"
        fi

        BACKEND_HTTP_STATUS=$(curl -sw "%{http_code}" -H "Host: $CONFIGURED_DOMAIN" http://127.0.0.1/api/system/safety-matrix -o /dev/null)
        if [ "$BACKEND_HTTP_STATUS" == "200" ]; then
            echo "PASS: Backend API (HTTP $BACKEND_HTTP_STATUS)"
        else
            echo "FAIL/WARNING: Backend API (HTTP $BACKEND_HTTP_STATUS)"
        fi
    else
        echo "No domain provided and no config found. Cannot test routes."
    fi
fi

echo "=========================================================="
