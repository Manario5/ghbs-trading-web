#!/bin/bash

echo "=========================================================="
echo " GHBS Private vs Public Exposure Check (Phase 6R) "
echo "=========================================================="

# Try to get public IP
PUBLIC_IP=$(curl -s -4 ifconfig.me || curl -s -4 icanhazip.com || hostname -I | awk '{print $1}')
echo "Detected Public IP: ${PUBLIC_IP:-UNKNOWN}"

TAILSCALE_IP=$(tailscale ip -4 2>/dev/null)
echo "Detected Tailscale IP: ${TAILSCALE_IP:-UNKNOWN}"

echo ""
echo "[Port Bindings Check]"
if command -v ss >/dev/null 2>&1; then
    echo "Checking 127.0.0.1 bindings (should be 8000, 3000):"
    ss -tlnp | grep -E '127\.0\.0\.1:(8000|3000)' || echo "   None found or not running."
    
    if [ -n "$TAILSCALE_IP" ]; then
        echo "Checking Tailscale IP bindings (should be $TAILSCALE_IP:8080):"
        ss -tlnp | grep "$TAILSCALE_IP:8080" || echo "   None found or not running."
    fi

    echo "Checking 0.0.0.0 or Public IP bindings (should NOT be 3000, 8000, 8080):"
    ss -tlnp | grep -E "(0\.0\.0\.0|::|${PUBLIC_IP}):(3000|8000|8080)" && echo "   WARNING: App ports exposed publicly!" || echo "   PASS: App ports not bound to 0.0.0.0."
else
    echo "ss command not found. Cannot check port bindings."
fi

echo ""
echo "[Public IP Exposure Test]"
if [ -n "$PUBLIC_IP" ] && [ "$PUBLIC_IP" != "UNKNOWN" ] && ! [[ "$PUBLIC_IP" =~ ^100\. ]]; then
    echo "Testing Public URL (http://$PUBLIC_IP:8080) - EXPECT CONNECTION REFUSED or TIMEOUT:"
    curl -m 3 -s -o /dev/null -w "%{http_code}" "http://$PUBLIC_IP:8080/" && echo "   WARNING: Public IP responded on 8080!" || echo "   PASS: Public IP did not respond on 8080."
    
    echo "Testing Public URL (http://$PUBLIC_IP:3000):"
    curl -m 3 -s -o /dev/null -w "%{http_code}" "http://$PUBLIC_IP:3000/" && echo "   WARNING: Public IP responded on 3000!" || echo "   PASS: Public IP did not respond on 3000."
    
    echo "Testing Public URL (http://$PUBLIC_IP:8000/api/system/safety-matrix):"
    curl -m 3 -s -o /dev/null -w "%{http_code}" "http://$PUBLIC_IP:8000/api/system/safety-matrix" && echo "   WARNING: Public API responded on 8000!" || echo "   PASS: Public API did not respond on 8000."
else
    echo "Unable to determine Public IP for testing."
fi

echo ""
echo "[Tailscale Private Access Test]"
if [ -n "$TAILSCALE_IP" ] && [ "$TAILSCALE_IP" != "UNKNOWN" ]; then
    echo "Testing Private URL (http://$TAILSCALE_IP:8080):"
    HTTP_FRONT=$(curl -s -m 5 -o /dev/null -w "%{http_code}" "http://$TAILSCALE_IP:8080/")
    if [ "$HTTP_FRONT" == "200" ]; then
        echo "   PASS: Private Frontend returned 200."
    else
        echo "   FAIL/WARNING: Private Frontend returned $HTTP_FRONT."
    fi

    echo "Testing Private API (http://$TAILSCALE_IP:8080/api/system/safety-matrix):"
    HTTP_BACK=$(curl -s -m 5 -o /dev/null -w "%{http_code}" "http://$TAILSCALE_IP:8080/api/system/safety-matrix")
    if [ "$HTTP_BACK" == "200" ]; then
        echo "   PASS: Private Backend returned 200."
        curl -s -m 5 "http://$TAILSCALE_IP:8080/api/system/safety-matrix" | grep -q '"safety_state":"SAFE"' && echo "   PASS: Safety Matrix safely confirms SAFE." || echo "   WARNING: Matrix explicitly NOT SAFE!"
    else
        echo "   FAIL/WARNING: Private Backend returned $HTTP_BACK."
    fi
else
    echo "Unable to determine Tailscale IP for testing."
fi

echo "=========================================================="
exit 0
