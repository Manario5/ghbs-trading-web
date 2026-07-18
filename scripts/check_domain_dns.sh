#!/bin/bash

DOMAIN=$1
EXPECTED_IP=$2

if [ -z "$DOMAIN" ]; then
    echo "ERROR: Domain argument required. Usage: ./scripts/check_domain_dns.sh DOMAIN [EXPECTED_IP]"
    exit 1
fi

if [[ "$DOMAIN" == "localhost" ]] || [[ "$DOMAIN" == "127.0.0.1" ]] || [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || [[ "$DOMAIN" == *"/"* ]] || [[ "$DOMAIN" == *":"* ]] || [[ "$DOMAIN" == "http://"* ]] || [[ "$DOMAIN" == "https://"* ]] || [[ "$DOMAIN" == "example.com" ]]; then
    echo "ERROR: Invalid domain: $DOMAIN"
    exit 1
fi

echo "Checking DNS resolution for $DOMAIN..."
if command -v dig >/dev/null 2>&1; then
    RESOLVED_IP=$(dig +short $DOMAIN | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -n 1)
elif command -v getent >/dev/null 2>&1; then
    RESOLVED_IP=$(getent hosts $DOMAIN | awk '{ print $1 }' | head -n 1)
elif command -v host >/dev/null 2>&1; then
    RESOLVED_IP=$(host $DOMAIN | grep 'has address' | awk '{ print $4 }' | head -n 1)
else
    echo "WARNING: No DNS lookup tools found (dig, getent, host)."
    exit 1
fi

if [ -z "$RESOLVED_IP" ]; then
    echo "FAIL: Could not resolve IP for $DOMAIN"
    exit 1
fi

echo "Resolved IP: $RESOLVED_IP"

if [ -n "$EXPECTED_IP" ]; then
    if [ "$RESOLVED_IP" == "$EXPECTED_IP" ]; then
        echo "PASS: Resolved IP matches expected IP ($EXPECTED_IP)."
    else
        echo "FAIL: Resolved IP ($RESOLVED_IP) does NOT match expected IP ($EXPECTED_IP)."
        exit 1
    fi
else
    echo "WARNING: No EXPECTED_IP provided. Please manually verify that $RESOLVED_IP points to this VPS!"
    echo "PASS (Unverified)"
fi
exit 0
