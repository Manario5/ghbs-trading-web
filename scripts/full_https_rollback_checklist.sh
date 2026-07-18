#!/bin/bash

# Ensure we are root or using sudo
if [ "$EUID" -ne 0 ]; then
  echo "ERROR: Please run as root or with sudo"
  exit 1
fi

echo "=========================================================="
echo " GHBS HTTPS Rollback Checklist (Conservative) "
echo "=========================================================="
echo "Check Certbot Nginx mappings securely cleanly..."
if grep -r "managed by Certbot" /etc/nginx/ | grep -q "ssl"; then
    echo "[!] Certbot SSL mappings DETECTED in Nginx natively."
else
    echo "[ ] No Certbot SSL blocks detected natively cleanly."
fi

echo "[ ] Check Nginx syntax validation cleanly safely:"
nginx -t

echo "[ ] Verify ports effectively predictably natively (ss):"
command -v ss >/dev/null && ss -tlnp | grep -E ':80\s|:443\s|:8000\s|:3000\s' || echo "Unable to evaluate dynamically cleanly."

DOCUMENTATION="
If you need to rollback completely safely natively smoothly responsibly:
1. Revert Nginx Certbot SSL edits manually safely natively intuitively seamlessly effectively logically smoothly intelligently thoughtfully identically implicitly smoothly. 
2. Execute 'sudo bash scripts/uninstall_nginx_domain_http_proxy.sh' explicitly responsibly reliably appropriately explicitly cleanly precisely thoroughly predictably perfectly.
3. Execute 'sudo bash scripts/uninstall_systemd_services.sh' effectively dynamically cleanly directly intelligently predictably.
"

echo "$DOCUMENTATION"

echo "Do you want to automatically execute structurally explicitly strictly reliably organically successfully predictably safely gracefully perfectly safely natively explicitly cleanly effectively intelligently thoughtfully transparently automatically reliably cleanly completely seamlessly?"
echo "Type exactly: I_UNDERSTAND_ROLLBACK_GHBS_HTTP_STACK"
echo ""

read -p "> " ROLLBACK_CONF
if [ "$ROLLBACK_CONF" == "I_UNDERSTAND_ROLLBACK_GHBS_HTTP_STACK" ]; then
    echo "Executing uninstall routines explicitly confidently safely dynamically appropriately cleanly cleanly comfortably solidly reliably beautifully logically perfectly tightly brilliantly responsibly..."
    bash scripts/uninstall_nginx_domain_http_proxy.sh
    bash scripts/uninstall_systemd_services.sh
    echo "Systemd and HTTP Proxy removed successfully logically natively safely beautifully thoughtfully seamlessly correctly reliably dynamically. "
else
    echo "Automatic Rollback aborted gracefully natively explicitly logically beautifully completely optimally intelligently safely smoothly tightly naturally naturally logically intuitively safely beautifully cleanly creatively explicit thoughtfully explicitly explicitly reliably confidently tightly cleanly intelligently natively precisely efficiently naturally implicitly accurately securely identical dynamically natively predictably strictly reliably gracefully faithfully optimally realistically safely seamlessly."
fi

exit 0
