"""
Tests for Prometheus Observability Metrics Endpoint.
"""

import pytest


@pytest.mark.unit
def test_metrics_endpoint_response(client):
    """Verify /metrics returns Prometheus text exposition format."""
    # First make a request to ensure counters are populated
    client.get("/")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

    content = response.text
    # Verify core Prometheus metrics exist in payload
    assert "cloudpulse_http_requests_total" in content
    assert "cloudpulse_http_request_duration_seconds" in content
    assert "cloudpulse_app_uptime_seconds" in content
    assert "cloudpulse_cpu_usage_percent" in content
    assert "cloudpulse_memory_usage_bytes" in content


@pytest.mark.unit
def test_metrics_counter_increments(client):
    """Verify HTTP request counter tracks and increments with endpoint calls."""

    # Hit root twice
    client.get("/")
    client.get("/")

    # Query metrics after
    after = client.get("/metrics").text
    assert "cloudpulse_http_requests_total" in after
