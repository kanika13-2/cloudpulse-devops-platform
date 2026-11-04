#!/usr/bin/env bash
# ==============================================================================
# CloudPulse Platform - Synthetic Traffic & Load Generator
# Sends concurrent requests to trigger HPA scaling & test Grafana/CloudWatch
# ==============================================================================

set -euo pipefail

TARGET_URL="${1:-http://localhost:8000}"
REQUEST_COUNT="${2:-100}"
CONCURRENCY="${3:-10}"

echo "================================================================"
echo "   CLOUDPULSE SYNTHETIC LOAD GENERATOR                          "
echo "   Target: ${TARGET_URL}/api/v1/simulate/load                   "
echo "   Requests: ${REQUEST_COUNT} | Concurrency: ${CONCURRENCY}     "
echo "================================================================"

simulate_request() {
    local id=$1
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${TARGET_URL}/api/v1/simulate/load?duration=0.2&intensity=100000" || echo "ERR")
    echo "Req #${id}: Status ${code}"
}

export -f simulate_request
export TARGET_URL

# Generate sequence and process with parallel or background subshells
seq 1 "${REQUEST_COUNT}" | xargs -P "${CONCURRENCY}" -I {} bash -c 'simulate_request "$@"' _ {}

echo ""
echo "Load generation completed. Check HPA status with:"
echo "kubectl get hpa -n cloudpulse --watch"

