<#
.SYNOPSIS
    CloudPulse Platform - Windows Local Development & Environment Setup Script
.DESCRIPTION
    Validates Python runtime, creates virtual environment, installs dependencies,
    executes the test suite, and provides launch instructions.
#>

[CmdletBinding()]
param (
    [switch]$SkipTests,
    [switch]$StartServer
)

$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   CLOUDPULSE PLATFORM - WINDOWS LOCAL SETUP                    " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 1. Verify Python Installation
Write-Host "`n[1/5] Verifying Python runtime..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.10+ from python.org"
    exit 1
}

# 2. Setup Virtual Environment
Write-Host "`n[2/5] Checking virtual environment (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment in .venv..." -ForegroundColor Gray
    python -m venv .venv
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "Existing virtual environment detected in .venv." -ForegroundColor Green
}

# Determine venv python path
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "python"
}

# 3. Upgrade pip and Install Dependencies
Write-Host "`n[3/5] Installing production & development dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r requirements-dev.txt
Write-Host "Dependencies successfully installed." -ForegroundColor Green

# 4. Execute Automated Unit Tests
if (-not $SkipTests) {
    Write-Host "`n[4/5] Executing automated unit test suite (pytest)..." -ForegroundColor Yellow
    & $venvPython -m pytest -v --tb=short
    if ($LASTEXITCODE -eq 0) {
        Write-Host "All unit tests passed successfully!" -ForegroundColor Green
    } else {
        Write-Warning "One or more tests failed! Review test outputs above."
    }
} else {
    Write-Host "`n[4/5] Skipping test execution (-SkipTests enabled)." -ForegroundColor Gray
}

# 5. Launch or Provide Instructions
Write-Host "`n[5/5] Environment Ready!" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "To activate virtual environment:" -ForegroundColor White
Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host "`nTo start CloudPulse API locally:" -ForegroundColor White
Write-Host "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Yellow
Write-Host "`nTo run full Docker Compose (App + Prometheus + Grafana):" -ForegroundColor White
Write-Host "  .\scripts\windows\docker-manage.ps1 -Action Up" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan

if ($StartServer) {
    Write-Host "`nStarting local development server..." -ForegroundColor Green
    & $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
}

