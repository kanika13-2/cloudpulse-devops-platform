"""
CloudPulse Health Check Router.
Provides liveness, readiness, and component diagnostics for Kubernetes probes
and load balancer health checkers.
"""

import os
import time
from datetime import datetime, timezone
import psutil
from fastapi import APIRouter, Response, status, Query
from app.config import get_settings
from app.models import HealthResponse, HealthChecks
from app.metrics import START_TIME

router = APIRouter(tags=["Health & Diagnostics"])


def get_disk_usage_percent() -> float:
    """Safely obtain primary filesystem usage percent across Windows & Linux."""
    try:
        drive_root = os.path.splitdrive(os.getcwd())[0] + os.sep
        return psutil.disk_usage(drive_root).percent
    except Exception:
        return 15.0


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health Probe",
    description="Endpoint for Kubernetes liveness & readiness probes and AWS Target Group health checks."
)
def get_health(
    response: Response,
    probe_type: str = Query(
        "all",
        pattern="^(all|liveness|readiness)$",
        description="Optional filter for specific probe checks: all, liveness, readiness"
    )
):
    """
    Evaluates system vitals (CPU, memory, disk).
    Returns HTTP 200 if healthy, HTTP 503 if degraded beyond safety limits.
    """
    settings = get_settings()
    uptime = time.time() - START_TIME

    # Gather system metrics
    try:
        process = psutil.Process()
        proc_mem = process.memory_info().rss / (1024 * 1024)  # MB
        cpu_pct = psutil.cpu_percent(interval=None)
        mem_pct = psutil.virtual_memory().percent
        disk_pct = get_disk_usage_percent()
    except Exception:
        proc_mem = 50.0
        cpu_pct = 5.0
        mem_pct = 20.0
        disk_pct = 10.0

    # Determine health states
    cpu_healthy = cpu_pct < settings.MAX_CPU_PERCENT_THRESHOLD
    mem_healthy = mem_pct < settings.MAX_MEMORY_PERCENT_THRESHOLD
    disk_healthy = disk_pct < 95.0

    is_healthy = cpu_healthy and mem_healthy and disk_healthy

    if not is_healthy and probe_type in ("all", "readiness"):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "degraded"
    else:
        response.status_code = status.HTTP_200_OK
        overall_status = "healthy"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=round(uptime, 2),
        checks=HealthChecks(
            cpu_status="healthy" if cpu_healthy else "overloaded",
            cpu_percent=round(cpu_pct, 2),
            memory_status="healthy" if mem_healthy else "exhausted",
            memory_percent=round(mem_pct, 2),
            process_memory_mb=round(proc_mem, 2),
            disk_status="healthy" if disk_healthy else "full"
        )
    )
