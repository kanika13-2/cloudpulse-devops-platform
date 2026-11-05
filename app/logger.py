"""
CloudPulse Structured Logging Engine.
Supports JSON-formatted output for AWS CloudWatch and local dev formatting,
with asynchronous context-aware correlation ID tracking.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict

# Context variable holding the correlation ID for the active request thread/task
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Retrieve current correlation ID or generate fallback."""
    cid = correlation_id_ctx.get()
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id_ctx.set(cid)
    return cid


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for CloudWatch & Fluent Bit ingestion."""

    def __init__(
        self, service_name: str = "cloudpulse-api", environment: str = "development"
    ):
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "environment": self.environment,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", get_correlation_id()),
            "source": f"{record.pathname}:{record.lineno}",
            "process_id": record.process,
            "thread_id": record.thread,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include custom extra fields if present
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            log_entry.update(extra)

        return json.dumps(log_entry)


class StandardFormatter(logging.Formatter):
    """Human-readable formatter with correlation ID for local terminal debugging."""

    def format(self, record: logging.LogRecord) -> str:
        cid = getattr(record, "correlation_id", get_correlation_id())
        cid_str = f"[{cid[:8]}]" if cid else "[-]"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"{timestamp} | {record.levelname:<8} | {cid_str} | {record.name} - {record.getMessage()}"


def setup_logger(
    name: str = "cloudpulse", log_level: str = "INFO", environment: str = "development"
) -> logging.Logger:
    """Configure and return an enterprise-ready logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if environment.lower() in ("production", "staging", "cloudwatch"):
        handler.setFormatter(
            JSONFormatter(service_name="cloudpulse-api", environment=environment)
        )
    else:
        handler.setFormatter(StandardFormatter())

    logger.addHandler(handler)
    logger.propagate = False
    return logger
