#!/bin/bash

echo "Running safety check..."

# Run the python script and preserve its exit code
python3 scripts/check_safety.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "Safety check failed! Backend might be unreachable or system is UNSAFE."
fi

exit $EXIT_CODE
