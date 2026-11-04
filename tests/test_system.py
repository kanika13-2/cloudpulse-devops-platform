"""
Tests for System Topology and Diagnostics Router.
"""

import pytest


@pytest.mark.unit
def test_system_info_endpoint(client):
    """Verify system diagnostics endpoint returns platform and host properties."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()

    assert "hostname" in data
    assert "os_name" in data
    assert "python_version" in data
    assert "cpu_count_logical" in data
    assert data["cpu_count_logical"] > 0
    assert "total_memory_mb" in data
    assert data["total_memory_mb"] > 0
    assert "aws_region" in data

