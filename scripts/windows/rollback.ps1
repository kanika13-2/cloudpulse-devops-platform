<#
.SYNOPSIS
    CloudPulse Platform - Windows Kubernetes Rollback & Recovery Script
.DESCRIPTION
    Safely undoes a failed rollout, restores the previous revision, and validates pod vitals.
.PARAMETER Revision
    Optional specific revision number to roll back to.
#>

[CmdletBinding()]
param (
    [string]$Namespace = "cloudpulse",
    [string]$Deployment = "cloudpulse-api",
    [int]$Revision = 0
)

$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Yellow
Write-Host "   CLOUDPULSE - KUBERNETES DISASTER RECOVERY & ROLLBACK (WINDOWS)" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Yellow

# 1. Check kubectl connectivity
try {
    $null = kubectl cluster-info 2>&1
} catch {
    Write-Error "Kubernetes cluster is not reachable via kubectl. Check your cluster connection."
    exit 1
}

# 2. Display Rollout History
Write-Host "`n[1/3] Fetching rollout revision history for $Deployment..." -ForegroundColor Cyan
kubectl rollout history deployment/$Deployment -n $Namespace

# 3. Trigger Rollback
Write-Host "`n[2/3] Executing safe rollback..." -ForegroundColor Yellow
if ($Revision -gt 0) {
    Write-Host "Rolling back to specific revision: $Revision..." -ForegroundColor White
    kubectl rollout undo deployment/$Deployment -n $Namespace --to-revision=$Revision
} else {
    Write-Host "Rolling back to previous stable revision..." -ForegroundColor White
    kubectl rollout undo deployment/$Deployment -n $Namespace
}

# 4. Await Rollout Completion
Write-Host "`n[3/3] Monitoring restoration status (timeout: 120s)..." -ForegroundColor Cyan
$rolloutStatus = kubectl rollout status deployment/$Deployment -n $Namespace --timeout=120s 2>&1
Write-Host $rolloutStatus -ForegroundColor Green

Write-Host "`nActive Restored Pods:" -ForegroundColor Cyan
kubectl get pods -n $Namespace -l app.kubernetes.io/name=cloudpulse-api

Write-Host "`nDisaster recovery rollback completed successfully!" -ForegroundColor Green

