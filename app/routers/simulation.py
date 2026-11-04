"""
CloudPulse Simulation Router.
Generates synthetic CPU load and deliberate error conditions to validate:
1. Kubernetes Horizontal Pod Autoscaling (HPA)
2. Prometheus error rate alerts
3. AWS CloudWatch metric alarms
"""

import time
import math
from fastapi import APIRouter, HTTPException, Query, status
from app.logger import setup_logger, get_correlation_id
from app.models import LoadSimulationResponse, ErrorSimulationResponse
from app.metrics import SIMULATED_ERRORS_TOTAL

logger = setup_logger()
router = APIRouter(prefix="/api/v1/simulate", tags=["DevOps Simulation"])


@router.post(
    "/load",
    response_model=LoadSimulationResponse,
    summary="Generate Synthetic CPU Load",
    description="Calculates mathematical series to generate measurable CPU load for HPA testing."
)
def simulate_load(
    duration: float = Query(0.5, ge=0.01, le=10.0, description="Duration to keep CPU busy (seconds)"),
    intensity: int = Query(500000, ge=1000, le=10000000, description="Iteration cycle count")
):
    """Executes floating point arithmetic to simulate computational workload."""
    start = time.time()
    total = 0.0

    # Run busy loop until duration is reached or iterations complete
    for i in range(intensity):
        total += math.sin(i) * math.cos(i)
        if (time.time() - start) >= duration:
            break

    elapsed = time.time() - start
    logger.info(
        f"Simulated load completed: duration={elapsed:.4f}s, iterations={intensity}",
        extra={"extra_fields": {"simulation_type": "cpu_load", "elapsed_seconds": elapsed}}
    )

    return LoadSimulationResponse(
        status="completed",
        duration_seconds=round(elapsed, 4),
        iterations=intensity,
        calculated_value=round(total, 4),
        message=f"Simulated CPU load ran for {elapsed:.4f}s"
    )


@router.get(
    "/error",
    response_model=ErrorSimulationResponse,
    summary="Simulate Application Error",
    description="Triggers a controlled 500 or 400 error to verify observability pipelines & alarms."
)
def simulate_error(
    error_type: str = Query("server_error", pattern="^(server_error|client_error|timeout)$"),
    status_code: int = Query(500, ge=400, le=599)
):
    """Triggers an error and records telemetry for alert validation."""
    cid = get_correlation_id()
    SIMULATED_ERRORS_TOTAL.labels(error_type=error_type).inc()

    logger.warning(
        f"Simulated error triggered: type={error_type}, status={status_code}, cid={cid}",
        extra={"extra_fields": {"simulation_type": "error", "error_type": error_type, "status_code": status_code}}
    )

    if status_code >= 500:
        raise HTTPException(
            status_code=status_code,
            detail={
                "status": "simulated_error",
                "error_code": status_code,
                "message": f"Simulated {error_type} triggered for CloudWatch/Prometheus alarm validation",
                "correlation_id": cid
            }
        )

    return ErrorSimulationResponse(
        status="simulated_warning",
        error_code=status_code,
        message=f"Simulated client condition triggered ({error_type})",
        correlation_id=cid
    )
