"""
FastAPI exception handlers — map domain errors to consistent HTTP responses.

Registers handlers for DomainError subclasses (404, 400, 401, 403, 409, 422)
as well as general ValueError → 400 and unhandled Exception → 500.

Usage in main.py::

    from core.exception_handlers import register_exception_handlers
    register_exception_handlers(app)
"""

from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from common.errors import (
    DomainError,
    NotFoundError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all domain-aware exception handlers to the FastAPI app."""

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        logger.warning(
            f"Domain error: {exc.message}",
            status_code=exc.status_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": type(exc).__name__,
                    "message": exc.message,
                    "detail": exc.detail,
                },
                "meta": {"requestId": getattr(request.state, "request_id", None)},
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        logger.warning(f"Validation error: {exc}", path=request.url.path)
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(exc),
                },
                "meta": {"requestId": getattr(request.state, "request_id", None)},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            f"Unhandled exception: {exc}",
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                },
                "meta": {"requestId": getattr(request.state, "request_id", None)},
            },
        )
