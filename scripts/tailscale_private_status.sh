#!/bin/bash

echo "=========================================================="
echo " GHBS Tailscale Private Access Status (Phase 6Q) "
echo "=========================================================="

# Tailscale check
if command -v tailscale >/dev/null 2>&1; then
    echo "Tailscale: INSTALLED"
    TS_STATUS=$(tailscale status | head -n 1)
    echo "Tailscale Status: $TS_STATUS"
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null)
    echo "Tailscale IPv4: ${TAILSCALE_IP:-NOT FOUND}"
else
    echo "Tailscale: NOT INSTALLED"
    TAILSCALE_IP=""
fi

echo ""
echo "[Systemd Status]"
if systemctl is-active --quiet ghbs-backend.service; then echo "Backend: RUNNING"; else echo "Backend: INACTIVE"; fi
if systemctl is-active --quiet ghbs-frontend.service; then echo "Frontend: RUNNING"; else echo "Frontend: INACTIVE"; fi

echo ""
echo "[Nginx Status]"
if systemctl is-active --quiet nginx; then echo "Nginx: RUNNING"; else echo "Nginx: INACTIVE"; fi

echo ""
echo "[Port 8080 Target]"
if [ -n "$TAILSCALE_IP" ]; then
    if command -v ss >/dev/null 2>&1; then
        ss -tlnp | grep -E "$TAILSCALE_IP:8080" || echo "Port 8080 NOT listening on $TAILSCALE_IP."
    else
        echo "Unable to deeply inspect ss binds locally."
    fi
else
    echo "Tailscale IP fundamentally missing. Can't check natively securely."
fi

echo ""
echo "[HTTP Tests]"
if [ -n "$TAILSCALE_IP" ]; then
    FRONTEND_HTTP_STATUS=$(curl -sw "%{http_code}" "http://$TAILSCALE_IP:8080/" -o /dev/null)
    if [ "$FRONTEND_HTTP_STATUS" == "200" ]; then
        echo "PASS: Frontend Route via Private IP (HTTP $FRONTEND_HTTP_STATUS)"
    else
        echo "FAIL/WARNING: Frontend Route via Private IP (HTTP $FRONTEND_HTTP_STATUS)"
    fi

    BACKEND_HTTP_STATUS=$(curl -sw "%{http_code}" "http://$TAILSCALE_IP:8080/api/system/safety-matrix" -o /dev/null)
    if [ "$BACKEND_HTTP_STATUS" == "200" ]; then
        echo "PASS: Backend API Route via Private IP (HTTP $BACKEND_HTTP_STATUS)"
        curl -s "http://$TAILSCALE_IP:8080/api/system/safety-matrix" | grep -q '"safety_state":"SAFE"' && echo "PASS: Safety Matrix natively securely SAFE." || echo "WARNING: Matrix explicitly NOT SAFE!"
    else
        echo "FAIL/WARNING: Backend API Route (HTTP $BACKEND_HTTP_STATUS)"
    fi
fi
echo "=========================================================="
exit 0
