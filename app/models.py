"""
CloudPulse Pydantic Schemas & Data Contracts.
"""

from typing import Optional
from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Root endpoint response model."""
    name: str = Field(..., examples=["CloudPulse"])
    description: str = Field(..., examples=["AWS Cloud Infrastructure & Intelligent DevOps Automation Platform"])
    version: str = Field(..., examples=["1.0.0"])
    environment: str = Field(..., examples=["production"])
    status: str = Field(..., examples=["healthy"])
    docs_url: str = Field(..., examples=["/docs"])
    health_url: str = Field(..., examples=["/health"])
    metrics_url: str = Field(..., examples=["/metrics"])


class HealthChecks(BaseModel):
    """Component-level health check states."""
    cpu_status: str = Field(..., examples=["healthy"])
    cpu_percent: float = Field(..., examples=[12.5])
    memory_status: str = Field(..., examples=["healthy"])
    memory_percent: float = Field(..., examples=[45.2])
    process_memory_mb: float = Field(..., examples=[64.8])
    disk_status: str = Field(..., examples=["healthy"])


class HealthResponse(BaseModel):
    """Health status response model for liveness and readiness probes."""
    status: str = Field(..., examples=["healthy"])
    timestamp: str = Field(..., examples=["2026-11-03T15:30:00Z"])
    version: str = Field(..., examples=["1.0.0"])
    environment: str = Field(..., examples=["production"])
    uptime_seconds: float = Field(..., examples=[3600.5])
    checks: HealthChecks


class SystemInfoResponse(BaseModel):
    """Host & runtime environment diagnostics."""
    hostname: str = Field(..., examples=["cloudpulse-pod-78df6f9-abc12"])
    os_name: str = Field(..., examples=["Linux"])
    os_release: str = Field(..., examples=["5.15.0-aws"])
    python_version: str = Field(..., examples=["3.12.2"])
    cpu_count_logical: int = Field(..., examples=[4])
    cpu_count_physical: Optional[int] = Field(None, examples=[2])
    total_memory_mb: float = Field(..., examples=[8192.0])
    available_memory_mb: float = Field(..., examples=[4096.0])
    aws_region: Optional[str] = Field(None, examples=["us-east-1"])


class LoadSimulationRequest(BaseModel):
    """Request model for CPU/traffic load simulation."""
    duration_seconds: float = Field(default=1.0, ge=0.01, le=30.0, description="Duration in seconds")
    intensity: int = Field(default=1000000, ge=1000, le=50000000, description="Iterations loop")


class LoadSimulationResponse(BaseModel):
    """Response model for CPU/traffic load simulation."""
    status: str = Field(..., examples=["completed"])
    duration_seconds: float = Field(..., examples=[1.0])
    iterations: int = Field(..., examples=[1000000])
    calculated_value: float = Field(..., examples=[499999500000.0])
    message: str = Field(..., examples=["Simulated CPU load executed successfully"])


class ErrorSimulationResponse(BaseModel):
    """Response model for error triggering simulation."""
    status: str = Field(..., examples=["simulated_error"])
    error_code: int = Field(..., examples=[500])
    message: str = Field(..., examples=["Simulated internal server error"])
    correlation_id: str = Field(..., examples=["9e2b102b-a01c-4b5c-a5b6-c6eb3c042e6f"])
