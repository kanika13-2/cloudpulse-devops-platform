#!/usr/bin/env bash
# ==============================================================================
# CloudPulse Platform - Linux Health & Diagnostic Probe Script
# Verifies /health, /metrics and Kubernetes Pod conditions
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${1:-http://localhost:8000}"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}   CLOUDPULSE HEALTH & OBSERVABILITY PROBE                      ${NC}"
echo -e "${BLUE}   Target Base URL: ${BASE_URL}                                 ${NC}"
echo -e "${BLUE}================================================================${NC}"

# 1. Probe Root Endpoint
echo -n "Checking Root Endpoint (/) ... "
ROOT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/" || echo "FAILED")
if [ "${ROOT_STATUS}" = "200" ]; then
    echo -e "${GREEN}OK (200)${NC}"
else
    echo -e "${RED}FAILED (${ROOT_STATUS})${NC}"
    exit 1
fi

# 2. Probe Deep Health Check Endpoint
echo -n "Checking Diagnostics Probe (/health) ... "
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/health" || echo "")
if [ -n "${HEALTH_RESPONSE}" ]; then
    HEALTH_STATUS=$(echo "${HEALTH_RESPONSE}" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    if [ "${HEALTH_STATUS}" = "healthy" ]; then
        echo -e "${GREEN}HEALTHY${NC}"
        echo "Diagnostics Payload:"
        echo "${HEALTH_RESPONSE}"
    else
        echo -e "${YELLOW}DEGRADED (${HEALTH_STATUS})${NC}"
        echo "${HEALTH_RESPONSE}"
        exit 1
    fi
else
    echo -e "${RED}UNREACHABLE${NC}"
    exit 1
fi

# 3. Probe Prometheus Metrics Endpoint
echo -n "Checking Metrics Exposition (/metrics) ... "
METRICS_RESPONSE=$(curl -s "${BASE_URL}/metrics" || echo "")
if echo "${METRICS_RESPONSE}" | grep -q "cloudpulse_http_requests_total"; then
    METRICS_COUNT=$(echo "${METRICS_RESPONSE}" | grep -v '^#' | grep -c '^cloudpulse' || echo 0)
    echo -e "${GREEN}OK (${METRICS_COUNT} metrics exported)${NC}"
else
    echo -e "${RED}METRICS NOT EXPOSED${NC}"
    exit 1
fi

# 4. Probe Kubernetes Pods (If kubectl available)
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
    echo ""
    echo -e "${BLUE}Checking Kubernetes Pod Status (namespace: cloudpulse)...${NC}"
    kubectl get pods -n cloudpulse -l app.kubernetes.io/name=cloudpulse-api
fi

echo ""
echo -e "${GREEN}SUCCESS: All CloudPulse platform health checks passed!${NC}"
exit 0

