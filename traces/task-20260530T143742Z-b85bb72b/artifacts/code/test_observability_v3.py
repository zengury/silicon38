"""
Unit tests for new v3 observability features:
  - REDMetrics convenience methods (track_latency, track_error, track_request)
  - PII-safe structured_log masking
  - HealthCheck registry
"""

import pytest
from infrastructure.observability.metrics import REDMetrics, MetricsRegistry, get_metrics
from infrastructure.observability.logging import structured_log, mask_pii_value, _is_sensitive_key
from infrastructure.observability.health import HealthCheck


class TestREDMetricsConvenience:
    """Verify track_latency, track_error, track_request convenience methods."""

    def test_track_request(self):
        red = REDMetrics("test")
        red.track_request()
        assert red.requests == 1
        assert red.errors == 0
        assert red.error_ratio == 0.0

    def test_track_latency(self):
        red = REDMetrics("test")
        red.track_latency(100.0)
        red.track_latency(200.0)
        assert red.requests == 2
        assert red.errors == 0
        assert red.avg_duration_ms == 150.0

    def test_track_error(self):
        red = REDMetrics("test")
        red.track_error("timeout")
        assert red.requests == 1
        assert red.errors == 1
        assert red.error_ratio == 1.0

    def test_mixed_usage(self):
        red = REDMetrics("test")
        red.track_request()  # success, no latency
        red.track_latency(50.0)  # success with latency
        red.track_error("dify_401")  # error
        assert red.requests == 3
        assert red.errors == 1
        assert red.error_ratio == 1 / 3
        assert red.avg_duration_ms == 50 / 3

    def test_error_ratio_zero_requests(self):
        red = REDMetrics("test")
        assert red.error_ratio == 0.0
        assert red.avg_duration_ms == 0.0

    def test_snapshot(self):
        red = REDMetrics("my_endpoint")
        red.track_latency(10.0)
        red.track_error("boom")
        snap = red.snapshot()
        assert snap["name"] == "my_endpoint"
        assert snap["requests"] == 2
        assert snap["errors"] == 1
        assert snap["error_ratio"] == 0.5
        assert snap["avg_duration_ms"] == 5.0

    def test_error_ratio_precision(self):
        """Error ratio should be rounded to 4 decimal places."""
        red = REDMetrics("test")
        red.track_request()
        red.track_request()
        red.track_error("x")
        assert red.error_ratio == 1 / 3
        snap = red.snapshot()
        assert snap["error_ratio"] == round(1 / 3, 4)

    def test_get_or_create_red(self):
        m = MetricsRegistry()
        red1 = m.get_or_create_red("agent_create")
        red1.track_latency(100.0)
        red2 = m.get_or_create_red("agent_create")
        assert red1 is red2
        assert red2.requests == 1


class TestPIIMasking:
    """Verify PII-safe logging — key redaction and value pattern masking."""

    def test_mask_email(self):
        result = mask_pii_value("alice@example.com")
        assert result == "***@***"

    def test_mask_email_in_text(self):
        result = mask_pii_value("Contact alice@example.com for help")
        assert "alice@example.com" not in result
        assert "***@***" in result

    def test_mask_cn_phone(self):
        result = mask_pii_value("13812345678")
        assert result == "138****5678"

    def test_mask_jwt(self):
        result = mask_pii_value("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dummy")
        assert result == "[JWT-REDACTED]"

    def test_non_string_not_masked(self):
        assert mask_pii_value(42) == "42"
        assert mask_pii_value(True) == "True"
        assert mask_pii_value(None) == "None"

    def test_sensitive_key_detection(self):
        assert _is_sensitive_key("password") is True
        assert _is_sensitive_key("PASSWORD") is True
        assert _is_sensitive_key("api_key") is True
        assert _is_sensitive_key("ACCESS_TOKEN") is True
        assert _is_sensitive_key("csrf_token") is True
        assert _is_sensitive_key("sender_password") is True
        assert _is_sensitive_key("user_name") is False
        assert _is_sensitive_key("robot_id") is False

    def test_long_value_truncation(self):
        long_val = "x" * 600
        result = mask_pii_value(long_val)
        assert "TRUNCATED" in result


class TestHealthCheck:
    """Verify HealthCheck registry behavior."""

    def test_all_healthy(self):
        hc = HealthCheck()
        hc.register("db", lambda: True, critical=True)
        hc.register("mqtt", lambda: True, critical=False)
        status, checks = hc.run_all()
        assert status == "healthy"
        assert checks["db"]["healthy"] is True
        assert checks["mqtt"]["healthy"] is True

    def test_critical_failure(self):
        hc = HealthCheck()
        hc.register("db", lambda: False, critical=True)
        hc.register("mqtt", lambda: True, critical=False)
        status, checks = hc.run_all()
        assert status == "unhealthy"

    def test_noncritical_failure(self):
        hc = HealthCheck()
        hc.register("db", lambda: True, critical=True)
        hc.register("mqtt", lambda: False, critical=False)
        status, checks = hc.run_all()
        assert status == "degraded"

    def test_exception_handling(self):
        hc = HealthCheck()
        hc.register("db", lambda: 1 / 0, critical=True)
        status, checks = hc.run_all()
        assert status == "unhealthy"
        assert "error" in checks["db"]
