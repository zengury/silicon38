"""
Unit tests for infrastructure.observability.metrics — MetricsRegistry.
"""

from infrastructure.observability.metrics import get_metrics, MetricsRegistry


class TestMetrics:
    """Verify thread-safe counter/gauges and RED metrics."""

    def test_increment_counter(self):
        m = MetricsRegistry()
        m.increment("test_total")
        assert m.get_counter("test_total") == 1
        m.increment("test_total")
        assert m.get_counter("test_total") == 2

    def test_set_gauge(self):
        m = MetricsRegistry()
        m.set_gauge("queue_depth", 42.0)
        assert m.get_gauge("queue_depth") == 42.0

    def test_red_metrics(self):
        m = MetricsRegistry()
        m.record_red("/users", "GET", 200, 15.5)
        m.record_red("/users", "GET", 500, 25.0)
        snap = m.snapshot()
        red = snap["red"]["GET:/users"]
        assert red["requests"] == 2
        assert red["errors"] == 1
        assert red["avg_duration_ms"] == 20.25

    def test_snapshot_is_read_only(self):
        m = MetricsRegistry()
        m.increment("a")
        snap = m.snapshot()
        snap["counters"]["a"] = 999
        assert m.get_counter("a") == 1

    def test_label_key_sorted(self):
        m = MetricsRegistry()
        m.increment("x", b="2", a="1")
        key = "x{a=1,b=2}"
        assert m.get_counter("x", a="1", b="2") == 1

    def test_counter_with_labels(self):
        m = MetricsRegistry()
        m.increment("login", result="success")
        m.increment("login", result="failure")
        assert m.get_counter("login", result="success") == 1
        assert m.get_counter("login", result="failure") == 1

    def test_gauge_default_zero(self):
        m = MetricsRegistry()
        assert m.get_gauge("nonexistent") == 0.0

    def test_counter_default_zero(self):
        m = MetricsRegistry()
        assert m.get_counter("nonexistent") == 0

    def test_global_singleton(self):
        m1 = get_metrics()
        m2 = get_metrics()
        assert m1 is m2
