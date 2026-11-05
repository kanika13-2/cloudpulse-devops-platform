"""
Tests for Root Application Endpoint.
"""

import pytest


@pytest.mark.unit
def test_root_endpoint_success(client):
    """Verify root endpoint returns 200 OK with correct system metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "CloudPulse"
    assert data["version"] == "1.0.0"
    assert data["status"] == "healthy"
    assert data["health_url"] == "/health"
    assert data["metrics_url"] == "/metrics"
    assert "X-Correlation-ID" in response.headers


@pytest.mark.unit
def test_custom_correlation_id_propagation(client):
    """Verify client-supplied correlation ID is preserved across request lifecycles."""
    custom_cid = "test-custom-uuid-12345"
    response = client.get("/", headers={"X-Correlation-ID": custom_cid})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_cid
