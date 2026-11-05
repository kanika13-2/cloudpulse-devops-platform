"""
CloudPulse Prometheus Observability Engine.
Defines metrics collectors for HTTP traffic, latency, application uptime,
system CPU, and memory utilization.
"""

import time
import psutil
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    REGISTRY,
)

# Application startup timestamp
START_TIME = time.time()

# --- Application Info Metric ---
APP_INFO = Info("cloudpulse_app", "Application metadata information", registry=REGISTRY)

# --- HTTP Request Metrics ---
HTTP_REQUESTS_TOTAL = Counter(
    "cloudpulse_http_requests_total",
    "Total count of HTTP requests processed by CloudPulse",
    ["method", "endpoint", "status"],
    registry=REGISTRY,
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "cloudpulse_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "cloudpulse_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
    registry=REGISTRY,
)

# --- System & Health Metrics ---
APP_UPTIME_SECONDS = Gauge(
    "cloudpulse_app_uptime_seconds",
    "Number of seconds the application has been running",
    registry=REGISTRY,
)

SYSTEM_CPU_PERCENT = Gauge(
    "cloudpulse_cpu_usage_percent",
    "Current process CPU utilization percentage",
    registry=REGISTRY,
)

SYSTEM_MEMORY_BYTES = Gauge(
    "cloudpulse_memory_usage_bytes",
    "Resident Set Size (RSS) memory in bytes",
    registry=REGISTRY,
)

SYSTEM_MEMORY_PERCENT = Gauge(
    "cloudpulse_memory_usage_percent",
    "System memory utilization percentage",
    registry=REGISTRY,
)

SIMULATED_ERRORS_TOTAL = Counter(
    "cloudpulse_simulated_errors_total",
    "Total count of simulated errors generated for alerting validation",
    ["error_type"],
    registry=REGISTRY,
)


def update_system_metrics() -> None:
    """Sample host/process CPU, memory, and uptime metrics before scraping."""
    APP_UPTIME_SECONDS.set(time.time() - START_TIME)
    try:
        process = psutil.Process()
        SYSTEM_CPU_PERCENT.set(process.cpu_percent(interval=None))
        mem_info = process.memory_info()
        SYSTEM_MEMORY_BYTES.set(mem_info.rss)
        SYSTEM_MEMORY_PERCENT.set(psutil.virtual_memory().percent)
    except Exception:
        # Fallback in environments with restricted proc access
        pass


def get_latest_metrics() -> bytes:
    """Refresh system gauges and return rendered Prometheus metric exposition payload."""
    update_system_metrics()
    return generate_latest(REGISTRY)
