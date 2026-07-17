#!/bin/bash

FORCE=$1

if [ "$FORCE" == "--force" ]; then
    echo "ERROR: Automated rollback via --force is unsafe for Certbot-managed files."
    echo "Certbot dynamically modifies the Nginx server blocks inline."
    echo "To roll back, you must manually edit the configuration."
fi

echo "========================================================"
echo " HTTPS / Certbot Rollback Instructions "
echo "========================================================"
echo "Certbot modifies Nginx configuration files by inserting"
echo "managed server blocks and SSL paths. To safely roll back:"
echo ""
echo "1. Edit /etc/nginx/sites-available/ghbs-trading-domain-http.conf"
echo "   (or wherever your domain config resides)."
echo "2. Remove the blocks marked with '# managed by Certbot'."
echo "3. Remove the 'listen 443 ssl' directives."
echo "4. Restore to the original Phase 6N template if necessary:"
echo "   sudo cp deploy/nginx-ghbs-domain-http.conf.example /etc/nginx/sites-available/ghbs-trading-domain-http.conf"
echo "   (ensure you replace __DOMAIN__ again)"
echo "5. Test the configuration: nginx -t"
echo "6. Reload Nginx: sudo systemctl reload nginx"
echo ""
echo "Note: The actual SSL certificates reside in /etc/letsencrypt/live/."
echo "You may optionally use 'sudo certbot delete' to remove them interactively."
echo "No Sandbox project files or databases have been destroyed."
echo "========================================================"
exit 0
