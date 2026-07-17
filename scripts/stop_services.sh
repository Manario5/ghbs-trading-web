#!/bin/bash

echo "Stopping GHBS Trading services..."

# Find and kill uvicorn backend processes safely
UVICORN_PIDS=$(pgrep -f "uvicorn backend.main:app")
if [ -n "$UVICORN_PIDS" ]; then
    echo "Stopping uvicorn backend processes: $UVICORN_PIDS"
    kill $UVICORN_PIDS
    echo "Backend stopped."
else
    echo "No uvicorn backend processes found."
fi

# Find and kill vite preview processes safely
VITE_PIDS=$(pgrep -f "vite preview")
if [ -n "$VITE_PIDS" ]; then
    echo "Stopping vite preview processes: $VITE_PIDS"
    kill $VITE_PIDS
    echo "Frontend stopped."
else
    echo "No vite preview processes found."
fi

echo "All app services stopped."
