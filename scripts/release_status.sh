#!/bin/bash

echo "==================================="
echo " GHBS Release Status "
echo "==================================="

echo ""
echo "[Process Status]"
UVICORN_PIDS=$(pgrep -f "uvicorn backend.main:app")
if [ -n "$UVICORN_PIDS" ]; then
    echo "Backend (uvicorn) is running. PIDs: $UVICORN_PIDS"
else
    echo "Backend (uvicorn) is NOT running."
fi

VITE_PIDS=$(pgrep -f "vite preview")
if [ -n "$VITE_PIDS" ]; then
    echo "Frontend (vite preview) is running. PIDs: $VITE_PIDS"
else
    echo "Frontend (vite preview) is NOT running."
fi

echo ""
echo "[Port Status]"
if command -v ss >/dev/null 2>&1; then
    ss -tlnp | grep -E ":8000|:3000" || echo "Ports 8000/3000 not listening."
elif command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep -E ":8000|:3000" || echo "Ports 8000/3000 not listening."
else
    echo "ss/netstat not available to check ports."
fi

echo ""
echo "[Safety Matrix Summary]"
./scripts/check_safety.sh || true

echo "==================================="
