"""
Metrics registry — in-process counters, gauges, and RED (Rate-Error-Duration)
metrics for operational monitoring.

Usage::

    from infrastructure.observability.metrics import get_metrics, REDMetrics

    metrics = get_metrics()
    metrics.increment("user_logins_total", result="success")

    red = REDMetrics("agent_create")
    red.track_request()          # count a request
    red.track_latency(234.5)     # record latency in ms
    red.track_error("timeout")   # record an error
"""

import threading
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class REDMetrics:
    """Rate-Error-Duration metrics for a single endpoint / operation.

    Args:
        name: Metric group name (e.g. ``"agent_create"``, ``"dify_api"``).

    Convenience methods:
        - ``track_request()`` — increment the request counter.
        - ``track_latency(ms)`` — record latency in milliseconds.
        - ``track_error(reason)`` — increment the error counter.
    """

    name: str = ""
    requests: int = 0
    errors: int = 0
    duration_ms_total: float = 0.0

    def track_request(self) -> None:
        """Record one request (success)."""
        self.requests += 1

    def track_latency(self, duration_ms: float) -> None:
        """Record latency for the current request.

        Args:
            duration_ms: Latency in milliseconds (float or int).
        """
        self.duration_ms_total += float(duration_ms)
        self.requests += 1

    def track_error(self, reason: str = "") -> None:
        """Record one error.

        Args:
            reason: Optional error category (e.g. ``"timeout"``, ``"dify_401"``).
                    Stored for inspection; not currently disaggregated.
        """
        self.errors += 1
        self.requests += 1

    @property
    def error_ratio(self) -> float:
        """Error ratio (0.0–1.0).  0.0 if no requests recorded."""
        if self.requests == 0:
            return 0.0
        return self.errors / self.requests

    @property
    def avg_duration_ms(self) -> float:
        """Average duration in milliseconds."""
        if self.requests == 0:
            return 0.0
        return self.duration_ms_total / self.requests

    def snapshot(self) -> dict:
        """Return a dict snapshot suitable for JSON serialization."""
        return {
            "name": self.name,
            "requests": self.requests,
            "errors": self.errors,
            "error_ratio": round(self.error_ratio, 4),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
        }


class MetricsRegistry:
    """Thread-safe in-memory metrics registry.

    Supports counter increments, gauge snapshots, and RED metrics tracking.
    Suitable for development, testing, and small-scale deployments.
    For production at scale, integrate with Prometheus / OpenTelemetry.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._red: Dict[str, REDMetrics] = {}

    # ── Counters ───────────────────────────────────────────────────────

    def increment(self, name: str, **labels) -> None:
        """Increment a counter by 1.

        Labels are appended to the metric key in Prometheus style:
        ``name{label1=val1,label2=val2}``.
        """
        key = _metric_key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + 1

    def increment_by(self, name: str, delta: int, **labels) -> None:
        """Increment a counter by *delta* (can be > 1)."""
        key = _metric_key(name, labels)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + delta

    def get_counter(self, name: str, **labels) -> int:
        """Read a counter value."""
        key = _metric_key(name, labels)
        with self._lock:
            return self._counters.get(key, 0)

    # ── Gauges ─────────────────────────────────────────────────────────

    def set_gauge(self, name: str, value: float, **labels) -> None:
        """Set a gauge to a specific value."""
        key = _metric_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def get_gauge(self, name: str, **labels) -> float:
        """Read a gauge value."""
        key = _metric_key(name, labels)
        with self._lock:
            return self._gauges.get(key, 0.0)

    # ── RED Metrics ────────────────────────────────────────────────────

    def get_or_create_red(self, name: str) -> REDMetrics:
        """Return (or create) a REDMetrics instance for *name*.

        Thread-safe.  Preferred over constructing ``REDMetrics(name)``
        directly when the instance must be shared across call sites.
        """
        with self._lock:
            if name not in self._red:
                self._red[name] = REDMetrics(name=name)
            return self._red[name]

    def record_red(
        self, endpoint: str, method: str, status_code: int, duration_ms: float
    ) -> None:
        """Record RED metrics for an HTTP endpoint call.

        Convenience wrapper that creates/increments a ``REDMetrics`` entry
        keyed by ``"{method}:{endpoint}"``.
        """
        key = f"{method}:{endpoint}"
        with self._lock:
            red = self._red.get(key)
            if red is None:
                red = REDMetrics(name=key)
                self._red[key] = red
            red.requests += 1
            if status_code >= 400:
                red.errors += 1
            red.duration_ms_total += duration_ms

    # ── Snapshot ───────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """Return a read-only snapshot of all metrics.

        Returns a dict with three keys:
          - ``counters``: dict of ``metric_name{labels}`` → value
          - ``gauges``: dict of ``metric_name{labels}`` → value
          - ``red``: dict of RED name → ``{"requests", "errors",
            "error_ratio", "avg_duration_ms"}``
        """
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "red": {k: v.snapshot() for k, v in self._red.items()},
            }


def _metric_key(name: str, labels: dict) -> str:
    """Build a Prometheus-style metric key from name and sorted labels."""
    if not labels:
        return name
    label_str = ",".join(
        f'{k}="{_escape_label(v)}"' for k, v in sorted(labels.items())
    )
    return f"{name}{{{label_str}}}"


def _escape_label(value) -> str:
    """Escape double-quotes and backslashes in label values."""
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


# ── Module-level singleton ─────────────────────────────────────────────

_metrics = MetricsRegistry()


def get_metrics() -> MetricsRegistry:
    """Return the global metrics registry singleton."""
    return _metrics
