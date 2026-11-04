"""
Pytest configuration and shared fixtures for CloudPulse tests.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings, get_settings


def get_test_settings() -> Settings:
    """Settings override for the testing environment."""
    return Settings(
        APP_NAME="CloudPulse-Test",
        ENVIRONMENT="test",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        AWS_REGION="us-east-1",
        AWS_CLOUDWATCH_ENABLED=False
    )


@pytest.fixture(scope="session")
def client():
    """Provides a synchronous FastAPI TestClient instance."""
    app.dependency_overrides[get_settings] = get_test_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

