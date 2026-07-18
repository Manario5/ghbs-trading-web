#!/bin/bash

# Ensure .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file is missing. Please copy .env.example to .env and configure it."
    exit 1
fi

echo "Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "Frontend build failed. Aborting startup."
    exit 1
fi

echo "Starting Frontend in PREVIEW mode..."
echo "Running on http://0.0.0.0:3000"

npx vite preview --host 0.0.0.0 --port 3000
