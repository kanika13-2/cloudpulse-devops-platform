#!/usr/bin/env bash
# ==============================================================================
# CloudPulse Platform - Linux Deployment Automation Script
# Validates prerequisites, builds container, applies manifests & verifies rollout
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

NAMESPACE="cloudpulse"
DEPLOYMENT_NAME="cloudpulse-api"
IMAGE_TAG="${1:-latest}"
IMAGE_NAME="cloudpulse-platform:${IMAGE_TAG}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# ------------------------------------------------------------------------------
# 1. Prerequisite Validation
# ------------------------------------------------------------------------------
log_info "Verifying deployment prerequisites..."

if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed or not in PATH. Please install kubectl."
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    log_error "Cannot reach Kubernetes cluster. Check current kubeconfig context."
    exit 1
fi

log_success "Kubernetes cluster connection verified."

# ------------------------------------------------------------------------------
# 2. Build Container Image (If Docker daemon available)
# ------------------------------------------------------------------------------
if command -v docker &> /dev/null && docker info &> /dev/null; then
    log_info "Building Docker image: ${IMAGE_NAME}..."
    docker build -t "${IMAGE_NAME}" .
    log_success "Docker image built successfully."
else
    log_warn "Docker daemon not accessible or not running. Skipping local build step."
fi

# ------------------------------------------------------------------------------
# 3. Apply Kubernetes Manifests in Order
# ------------------------------------------------------------------------------
log_info "Applying Kubernetes manifests to namespace: ${NAMESPACE}..."

kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-secret.yaml
kubectl apply -f k8s/07-serviceaccount.yaml
kubectl apply -f k8s/03-deployment.yaml
kubectl apply -f k8s/04-service.yaml
kubectl apply -f k8s/05-hpa.yaml
kubectl apply -f k8s/06-pdb.yaml
kubectl apply -f k8s/08-ingress.yaml

log_success "Manifests applied successfully."

# ------------------------------------------------------------------------------
# 4. Monitor & Await Zero-Downtime Rolling Update
# ------------------------------------------------------------------------------
log_info "Awaiting rolling update completion (timeout: 120s)..."

if kubectl rollout status deployment/"${DEPLOYMENT_NAME}" -n "${NAMESPACE}" --timeout=120s; then
    log_success "Deployment rollout completed with 100% readiness."
else
    log_error "Deployment rollout failed or timed out! Initiating safety inspection..."
    kubectl describe deployment "${DEPLOYMENT_NAME}" -n "${NAMESPACE}"
    kubectl get pods -n "${NAMESPACE}"
    exit 1
fi

# ------------------------------------------------------------------------------
# 5. Summary & Health Status Output
# ------------------------------------------------------------------------------
echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}   CLOUDPULSE PLATFORM DEPLOYED SUCCESSFULLY                     ${NC}"
echo -e "${GREEN}================================================================${NC}"
kubectl get pods -n "${NAMESPACE}" -l app.kubernetes.io/name=cloudpulse-api
echo ""
kubectl get svc -n "${NAMESPACE}"
echo ""
log_info "To test port-forwarding locally, run:"
echo "kubectl port-forward -n ${NAMESPACE} svc/cloudpulse-service 8000:80"

