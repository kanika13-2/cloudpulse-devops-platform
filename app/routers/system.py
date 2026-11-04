"""
CloudPulse System Diagnostics Router.
Provides platform, host, and cloud environment details.
"""

import platform
import socket
import psutil
from fastapi import APIRouter
from app.config import get_settings
from app.models import SystemInfoResponse

router = APIRouter(prefix="/api/v1/system", tags=["System Diagnostics"])


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    summary="Host & Runtime Details",
    description="Inspect host system topology, OS, CPU cores, memory limits, and AWS Region."
)
def get_system_info():
    """Returns runtime host metrics for container/node verification in EKS."""
    settings = get_settings()
    vm = psutil.virtual_memory()

    return SystemInfoResponse(
        hostname=socket.gethostname(),
        os_name=platform.system(),
        os_release=platform.release(),
        python_version=platform.python_version(),
        cpu_count_logical=psutil.cpu_count(logical=True) or 1,
        cpu_count_physical=psutil.cpu_count(logical=False),
        total_memory_mb=round(vm.total / (1024 * 1024), 2),
        available_memory_mb=round(vm.available / (1024 * 1024), 2),
        aws_region=settings.AWS_REGION
    )

