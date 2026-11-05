"""
Tests for Structured Logging and Correlation ID tracking.
"""

import json
import logging
from app.logger import (
    JSONFormatter,
    StandardFormatter,
    correlation_id_ctx,
)


def test_json_formatter():
    """Verify JSONFormatter creates valid parseable JSON with required cloud fields."""
    formatter = JSONFormatter(service_name="cloudpulse-test", environment="test")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="Test log message",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["service"] == "cloudpulse-test"
    assert parsed["environment"] == "test"
    assert parsed["message"] == "Test log message"
    assert "timestamp" in parsed
    assert "correlation_id" in parsed


def test_standard_formatter():
    """Verify StandardFormatter includes timestamp, level, and correlation ID."""
    formatter = StandardFormatter()
    token = correlation_id_ctx.set("abcdef12-3456-7890")
    try:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="test.py",
            lineno=10,
            msg="Console warning message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "WARNING" in output
        assert "Console warning message" in output
        assert "[abcdef12]" in output
    finally:
        correlation_id_ctx.reset(token)
