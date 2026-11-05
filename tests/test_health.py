"""
Tests for Health and Diagnostic Endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
def test_health_endpoint_healthy(client):
    """Verify health endpoint returns 200 with complete diagnostics when resources are within bounds."""
    mock_vm = MagicMock()
    mock_vm.percent = 45.0

    mock_process = MagicMock()
    mock_mem_info = MagicMock()
    mock_mem_info.rss = 64 * 1024 * 1024  # 64 MB
    mock_process.memory_info.return_value = mock_mem_info

    with patch("psutil.virtual_memory", return_value=mock_vm), patch(
        "psutil.cpu_percent", return_value=15.0
    ), patch("psutil.Process", return_value=mock_process), patch(
        "app.routers.health.get_disk_usage_percent", return_value=40.0
    ):

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0.0

        checks = data["checks"]
        assert checks["cpu_status"] == "healthy"
        assert checks["memory_status"] == "healthy"
        assert checks["disk_status"] == "healthy"
        assert checks["process_memory_mb"] == 64.0


@pytest.mark.unit
def test_health_probe_type_liveness(client):
    """Verify liveness probe returns 200 even under degraded condition."""
    response = client.get("/health?probe_type=liveness")
    assert response.status_code == 200
    data = response.json()
    assert "checks" in data


@pytest.mark.unit
def test_health_degraded_scenario(client):
    """Verify health probe marks status 503 when memory exceeds threshold."""

    class MockVirtualMemory:
        percent = 98.5

    with patch("psutil.virtual_memory", return_value=MockVirtualMemory()):
        response = client.get("/health?probe_type=readiness")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["memory_status"] == "exhausted"
