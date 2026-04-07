#!/bin/bash
# Wait for the API to be healthy before starting the apps/web
# This prevents the "Unable to Connect to API Server" error during startup

API_URL="${INTERNAL_API_URL:-http://localhost:5055}"
MAX_RETRIES=60  # 60 retries * 5 seconds = 5 minutes max wait
RETRY_INTERVAL=5

echo "Waiting for API to be ready at ${API_URL}/health..."

for i in $(seq 1 $MAX_RETRIES); do
    if curl -s -f "${API_URL}/health" > /dev/null 2>&1; then
        echo "API is ready! Starting apps/web..."
        exit 0
    fi
    echo "Attempt $i/$MAX_RETRIES: API not ready yet, waiting ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

echo "ERROR: API did not become ready within $((MAX_RETRIES * RETRY_INTERVAL)) seconds"
exit 1
