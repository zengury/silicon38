"""
HTTP middleware — correlation IDs, request logging, response timing.

Usage in main.py::

    from infrastructure.observability.middleware import add_correlation_middleware
    add_correlation_middleware(app)
"""

import time
import uuid

from fastapi import FastAPI, Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.observability.logging import structured_log
from infrastructure.observability.metrics import get_metrics


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID and log every request/response cycle.

    - Reads ``X-Request-ID`` from incoming requests; generates one if missing.
    - Attaches ``request.state.correlation_id`` for downstream use.
    - Binds the correlation ID into the loguru context so that every
      ``structured_log()`` call during this request carries it.
    - Records RED metrics (rate, errors, duration) per HTTP path.
    - Returns ``X-Request-ID`` in the response header.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(
            "X-Request-ID", request.headers.get("X-Correlation-Id", "")
        ) or str(uuid.uuid4())[:8]
        request.state.correlation_id = request_id

        start = time.perf_counter()

        with logger.contextualize(correlation_id=request_id):
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            structured_log(
                "INFO",
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms,
            )

            # Record RED metrics
            get_metrics().record_red(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

        response.headers["X-Request-ID"] = request_id
        return response


def add_correlation_middleware(app: FastAPI) -> None:
    """Attach correlation ID + request-logging + RED middleware to *app*."""
    app.add_middleware(CorrelationMiddleware)
