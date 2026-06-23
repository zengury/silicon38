"""
Health-check endpoints for Kubernetes liveness/readiness probes and
in-process metrics exposure.

Usage in main.py::

    from infrastructure.observability.health import build_health_router
    app.include_router(build_health_router(db_engine=engine, mqtt_client=client))

Endpoints:
  - ``GET /health/live`` — liveness probe (always alive if process running).
  - ``GET /health/ready`` — readiness probe (DB + MQTT connectivity).
  - ``GET /health/metrics`` — in-process metrics snapshot.
"""

from fastapi import APIRouter, HTTPException
from sqlmodel import text
from loguru import logger

from infrastructure.observability.metrics import get_metrics


class HealthCheck:
    """Registry for named dependency health checks.

    Usage::

        health = HealthCheck()
        health.register("database", check_db, critical=True)
        health.register("mqtt", check_mqtt, critical=False)

        status, checks = health.run_all()
        # status: "healthy" | "degraded" | "unhealthy"
    """

    def __init__(self):
        self._checks: dict[
            str, tuple[callable, bool]
        ] = {}  # name → (callable, is_critical)

    def register(self, name: str, check_fn, *, critical: bool = True) -> None:
        """Register a health check function.

        Args:
            name: Display name (e.g. ``"database"``).
            check_fn: Callable that returns ``True`` (healthy) or
                       ``False`` / raises (unhealthy).
            critical: If ``True``, a failure marks the service ``"unhealthy"``.
                       If ``False``, a failure results in ``"degraded"``.
        """
        self._checks[name] = (check_fn, critical)

    def run_all(self) -> tuple[str, dict]:
        """Run all registered checks.

        Returns:
            ``(status, checks_dict)`` where *status* is one of
            ``"healthy"``, ``"degraded"``, ``"unhealthy"``.
        """
        results: dict[str, dict] = {}
        any_critical_fail = False
        any_noncritical_fail = False

        for name, (check_fn, critical) in self._checks.items():
            try:
                ok = check_fn()
                results[name] = {"healthy": bool(ok), "critical": critical}
                if not ok:
                    if critical:
                        any_critical_fail = True
                    else:
                        any_noncritical_fail = True
            except Exception as exc:
                results[name] = {
                    "healthy": False,
                    "critical": critical,
                    "error": str(exc),
                }
                if critical:
                    any_critical_fail = True
                else:
                    any_noncritical_fail = True

        if any_critical_fail:
            status = "unhealthy"
        elif any_noncritical_fail:
            status = "degraded"
        else:
            status = "healthy"

        return status, results


def _build_default_checks(db_engine=None, mqtt_client=None) -> HealthCheck:
    """Register built-in health checks for database and MQTT."""
    health = HealthCheck()

    if db_engine is not None:

        def check_db():
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True

        health.register("database", check_db, critical=True)

    if mqtt_client is not None:

        def check_mqtt():
            return bool(getattr(mqtt_client, "is_connected", lambda: False)())

        health.register("mqtt", check_mqtt, critical=False)

    return health


def build_health_router(
    db_engine=None,
    mqtt_client=None,
) -> APIRouter:
    """Return a FastAPI router with liveness, readiness, and metrics endpoints.

    Args:
        db_engine: SQLAlchemy engine (optional — DB check registered if provided).
        mqtt_client: MQTT client instance (optional — MQTT check registered if provided).
    """
    router = APIRouter(prefix="/health", tags=["health"])
    health_registry = _build_default_checks(db_engine, mqtt_client)

    @router.get("/live")
    async def liveness():
        """Liveness probe — returns 200 if the process is alive."""
        return {"status": "alive", "service": "roboease-backend"}

    @router.get("/ready")
    async def readiness():
        """Readiness probe — checks database and MQTT connectivity."""
        status, checks = health_registry.run_all()

        if status == "healthy":
            return {
                "status": "healthy",
                "checks": {
                    name: {"healthy": info["healthy"]}
                    for name, info in checks.items()
                },
            }
        elif status == "degraded":
            return {
                "status": "degraded",
                "checks": {
                    name: {
                        "healthy": info["healthy"],
                        **(info.get("error") and {"error": info["error"]} or {}),
                    }
                    for name, info in checks.items()
                },
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "checks": {
                        name: {
                            "healthy": info["healthy"],
                            "critical": info["critical"],
                            **(info.get("error") and {"error": info["error"]} or {}),
                        }
                        for name, info in checks.items()
                    },
                },
            )

    @router.get("/metrics")
    async def metrics():
        """Return an in-process metrics snapshot.

        Format::

            {
              "uptime_seconds": 1234.5,
              "counters": { "metric_name{labels}": value, ... },
              "gauges":   { "metric_name{labels}": value, ... },
              "red":      { "red_name": { "requests": N, "errors": N, ... }, ... }
            }
        """
        import time as _time

        metrics_snapshot = get_metrics().snapshot()
        metrics_snapshot["uptime_seconds"] = round(_time.monotonic(), 1)
        return metrics_snapshot

    return router
