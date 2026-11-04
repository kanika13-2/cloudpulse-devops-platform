<#
.SYNOPSIS
    CloudPulse Platform - Windows Docker & Docker Compose Management Script
.DESCRIPTION
    Builds, starts, stops, logs, and verifies the multi-container stack.
.PARAMETER Action
    Build, Up, Down, Status, Logs, or Test.
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("Build", "Up", "Down", "Status", "Logs", "Test")]
    [string]$Action
)

$ErrorActionPreference = "Stop"

function Check-Docker {
    try {
        $null = docker --version 2>&1
    } catch {
        Write-Error "Docker is not installed or not in PATH. Please start Docker Desktop."
        exit 1
    }
}

switch ($Action) {
    "Build" {
        Check-Docker
        Write-Host "Building CloudPulse multi-stage Docker image..." -ForegroundColor Cyan
        docker build -t cloudpulse-platform:latest .
        Write-Host "Docker image built successfully." -ForegroundColor Green
    }

    "Up" {
        Check-Docker
        Write-Host "Starting CloudPulse, Prometheus, and Grafana via Docker Compose..." -ForegroundColor Cyan
        docker compose up -d --build
        Write-Host "`nWaiting 10s for services to initialize..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        Write-Host "`nService Endpoints:" -ForegroundColor Green
        Write-Host "  - CloudPulse API:  http://localhost:8000" -ForegroundColor White
        Write-Host "  - Health Probe:    http://localhost:8000/health" -ForegroundColor White
        Write-Host "  - Metrics:         http://localhost:8000/metrics" -ForegroundColor White
        Write-Host "  - Prometheus UI:   http://localhost:9090" -ForegroundColor White
        Write-Host "  - Grafana UI:      http://localhost:3000 (admin/admin)" -ForegroundColor White
    }

    "Down" {
        Check-Docker
        Write-Host "Stopping and tearing down CloudPulse Docker Compose stack..." -ForegroundColor Yellow
        docker compose down -v
        Write-Host "All containers and volumes stopped." -ForegroundColor Green
    }

    "Status" {
        Check-Docker
        Write-Host "CloudPulse Container Status:" -ForegroundColor Cyan
        docker compose ps
    }

    "Logs" {
        Check-Docker
        docker compose logs -f --tail=100
    }

    "Test" {
        Check-Docker
        Write-Host "Executing Health Verification against running containers..." -ForegroundColor Cyan
        & ".\scripts\windows\health-check.ps1"
    }
}

