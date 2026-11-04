#!/usr/bin/env bash
# ==============================================================================
# CloudPulse Platform - Linux Safe Automated Rollback Script
# Automatically rolls back bad deployment, monitors stability & validates health
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

NAMESPACE="cloudpulse"
DEPLOYMENT_NAME="cloudpulse-api"
TARGET_REVISION="${1:-}"

log_info() { echo -e "${BLUE}[INFO]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"; }

echo -e "${YELLOW}================================================================${NC}"
echo -e "${YELLOW}   CLOUDPULSE AUTOMATED DISASTER RECOVERY & ROLLBACK            ${NC}"
echo -e "${YELLOW}================================================================${NC}"

# 1. Verify Cluster Connectivity
if ! command -v kubectl &> /dev/null || ! kubectl cluster-info &> /dev/null; then
    log_error "Kubernetes cluster is not reachable via kubectl."
    exit 1
fi

# 2. Display Rollout History
log_info "Fetching rollout revision history for ${DEPLOYMENT_NAME}..."
kubectl rollout history deployment/"${DEPLOYMENT_NAME}" -n "${NAMESPACE}"

# 3. Execute Rollback
if [ -n "${TARGET_REVISION}" ]; then
    log_warn "Initiating targeted rollback to revision ${TARGET_REVISION}..."
    kubectl rollout undo deployment/"${DEPLOYMENT_NAME}" -n "${NAMESPACE}" --to-revision="${TARGET_REVISION}"
else
    log_warn "Initiating rollback to previous stable revision..."
    kubectl rollout undo deployment/"${DEPLOYMENT_NAME}" -n "${NAMESPACE}"
fi

# 4. Await Rollout Restoration
log_info "Monitoring rollback restoration status (timeout: 120s)..."
if kubectl rollout status deployment/"${DEPLOYMENT_NAME}" -n "${NAMESPACE}" --timeout=120s; then
    log_success "Rollback successfully applied and verified."
else
    log_error "Rollback failed to stabilize! Checking pod failure causes..."
    kubectl describe deployment "${DEPLOYMENT_NAME}" -n "${NAMESPACE}"
    kubectl get pods -n "${NAMESPACE}"
    exit 1
fi

# 5. Pod Vitals After Recovery
log_info "Restored Pod Instances:"
kubectl get pods -n "${NAMESPACE}" -l app.kubernetes.io/name=cloudpulse-api

log_success "Disaster recovery rollback completed successfully."

