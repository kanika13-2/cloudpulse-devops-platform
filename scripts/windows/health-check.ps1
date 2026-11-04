<#
.SYNOPSIS
    CloudPulse Platform - Windows PowerShell Health Check Script
.DESCRIPTION
    Validates /health, /metrics, and / endpoints using native PowerShell cmdlets.
.PARAMETER BaseUrl
    Base URL of the running application. Defaults to http://localhost:8000.
#>

[CmdletBinding()]
param (
    [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Continue"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   CLOUDPULSE PLATFORM - HEALTH & OBSERVABILITY PROBE           " -ForegroundColor Cyan
Write-Host "   Target: $BaseUrl                                             " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 1. Test Root Discovery Endpoint
Write-Host "`n[1/3] Testing Root Endpoint ($BaseUrl/) ..." -NoNewline
try {
    $root = Invoke-RestMethod -Uri "$BaseUrl/" -Method Get -TimeoutSec 5
    Write-Host " [PASS] (200 OK)" -ForegroundColor Green
    Write-Host "  Application: $($root.name) v$($root.version) ($($root.environment))" -ForegroundColor Gray
} catch {
    Write-Host " [FAIL] $_" -ForegroundColor Red
    exit 1
}

# 2. Test Deep Health Endpoint
Write-Host "`n[2/3] Testing Health Diagnostics ($BaseUrl/health) ..." -NoNewline
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 5
    if ($health.status -eq "healthy") {
        Write-Host " [HEALTHY] (200 OK)" -ForegroundColor Green
    } else {
        Write-Host " [DEGRADED: $($health.status)]" -ForegroundColor Yellow
    }
    Write-Host "  Uptime:             $($health.uptime_seconds)s" -ForegroundColor Gray
    Write-Host "  CPU Status:         $($health.checks.cpu_status) ($($health.checks.cpu_percent)%)" -ForegroundColor Gray
    Write-Host "  Memory Status:      $($health.checks.memory_status) ($($health.checks.memory_percent)%)" -ForegroundColor Gray
    Write-Host "  Process Memory RSS: $($health.checks.process_memory_mb) MB" -ForegroundColor Gray
    Write-Host "  Disk Status:        $($health.checks.disk_status)" -ForegroundColor Gray
} catch {
    Write-Host " [FAIL] $_" -ForegroundColor Red
    exit 1
}

# 3. Test Prometheus Metrics Exposition
Write-Host "`n[3/3] Testing Prometheus Metrics ($BaseUrl/metrics) ..." -NoNewline
try {
    $metrics = Invoke-WebRequest -Uri "$BaseUrl/metrics" -Method Get -TimeoutSec 5
    if ($metrics.Content -match "cloudpulse_http_requests_total") {
        Write-Host " [PASS] (Prometheus format verified)" -ForegroundColor Green
        $sampleLines = ($metrics.Content -split "`n" | Where-Object { $_ -match "^cloudpulse_" } | Select-Object -First 4)
        Write-Host "  Sample Telemetry Metrics:" -ForegroundColor Gray
        foreach ($line in $sampleLines) {
            Write-Host "    $line" -ForegroundColor DarkGray
        }
    } else {
        Write-Host " [FAIL] Output does not contain cloudpulse metric signatures" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host " [FAIL] $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n================================================================" -ForegroundColor Green
Write-Host "   ALL CLOUDPULSE HEALTH & DIAGNOSTIC CHECKS PASSED             " -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green

