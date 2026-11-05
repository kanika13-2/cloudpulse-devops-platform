"""
Tests for Load and Error Simulation Routers.
"""

import pytest


@pytest.mark.unit
def test_simulate_load_execution(client):
    """Verify load simulation runs and returns execution statistics."""
    response = client.post("/api/v1/simulate/load?duration=0.05&intensity=5000")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert data["duration_seconds"] >= 0.0
    assert data["iterations"] == 5000
    assert "calculated_value" in data


@pytest.mark.unit
def test_simulate_error_server(client):
    """Verify simulate error returns expected 500 status code and correlation ID."""
    response = client.get(
        "/api/v1/simulate/error?error_type=server_error&status_code=500"
    )
    assert response.status_code == 500
    data = response.json()

    assert "detail" in data
    assert data["detail"]["error_code"] == 500
    assert "correlation_id" in data["detail"]


@pytest.mark.unit
def test_simulate_error_client_warning(client):
    """Verify simulate error with client error returns 200 response payload with warning status."""
    response = client.get(
        "/api/v1/simulate/error?error_type=client_error&status_code=400"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "simulated_warning"
    assert data["error_code"] == 400
    assert "correlation_id" in data
