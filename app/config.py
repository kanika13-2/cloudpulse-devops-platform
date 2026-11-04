"""
CloudPulse Configuration Module.
Centralizes environment settings, AWS configuration, and observability flags.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings backed by environment variables."""

    # Application Metadata
    APP_NAME: str = "CloudPulse"
    APP_DESCRIPTION: str = "AWS Cloud Infrastructure & Intelligent DevOps Automation Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    LOG_LEVEL: str = "INFO"

    # AWS Configuration (Configurable & Completely Optional for Local Development)
    AWS_REGION: str = "us-east-1"
    AWS_ACCOUNT_ID: Optional[str] = None
    AWS_ECR_REPOSITORY: str = "cloudpulse-platform"
    AWS_EKS_CLUSTER_NAME: str = "cloudpulse-eks-cluster"
    AWS_CLOUDWATCH_ENABLED: bool = False
    AWS_CLOUDWATCH_LOG_GROUP: str = "/aws/eks/cloudpulse/application"

    # Health Check Thresholds
    MAX_MEMORY_PERCENT_THRESHOLD: float = 96.0
    MAX_CPU_PERCENT_THRESHOLD: float = 95.0

    # Prometheus Observability
    METRICS_ENABLED: bool = True
    METRICS_PATH: str = "/metrics"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
