#!/bin/bash

echo "================================================="
echo " GHBS Systemd Services Status (Sandbox Phase 6L) "
echo "================================================="

echo ""
echo "[Service States]"
if systemctl is-active --quiet ghbs-backend.service; then
    echo "Backend (ghbs-backend.service): RUNNING"
else
    echo "Backend (ghbs-backend.service): STOPPED / FAIL / INACTIVE"
fi

if systemctl is-active --quiet ghbs-frontend.service; then
    echo "Frontend (ghbs-frontend.service): RUNNING"
else
    echo "Frontend (ghbs-frontend.service): STOPPED / FAIL / INACTIVE"
fi

echo ""
echo "[Port Status (8000/3000)]"
if command -v ss >/dev/null 2>&1; then
    ss -tlnp | grep -E ":8000|:3000" || echo "Ports 8000/3000 not actively listening via ss."
elif command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep -E ":8000|:3000" || echo "Ports 8000/3000 not actively listening via netstat."
else
    echo "ss/netstat network utilities aren't strictly available to inspect local ports quickly."
fi

echo ""
echo "[Safety Matrix Enforcement Baseline]"
if systemctl is-active --quiet ghbs-backend.service; then
    ./scripts/check_safety.sh || echo "WARNING: Check Safety routine returned an error limit natively."
else
    echo "NOTICE: Safety matrix bypassed dynamically since backend server is structurally stopped right now."
fi

echo "================================================="
