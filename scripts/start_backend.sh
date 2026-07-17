#!/bin/bash

# Ensure .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file is missing. Please copy .env.example to .env and configure it."
    exit 1
fi

# Activate venv if present
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export PYTHONPATH=$(pwd)

echo "Starting Backend API in RELEASE mode..."
echo "Running on http://127.0.0.1:8000"
echo "(No auto-reload enabled. For dev mode, use uvicorn backend.main:app --reload)"

# Start uvicorn without --reload, bind to 127.0.0.1:8000
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
