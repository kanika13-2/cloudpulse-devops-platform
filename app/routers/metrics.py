"""
CloudPulse Metrics Exposition Router.
Exposes Prometheus telemetry in standard OpenMetrics / Prometheus text format.
"""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST
from app.metrics import get_latest_metrics

router = APIRouter(tags=["Observability & Metrics"])


@router.get(
    "/metrics",
    summary="Prometheus Metrics Exposition",
    description="Endpoint scraped by Prometheus or AWS CloudWatch Prometheus agent.",
)
def get_metrics():
    """Generates latest application and system Prometheus metrics."""
    metrics_data = get_latest_metrics()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
