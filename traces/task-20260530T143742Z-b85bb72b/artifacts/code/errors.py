"""
Domain and infrastructure exception classes for RoboEase backend.

All custom errors extend from DomainError so that the exception handler
middleware can map them to appropriate HTTP status codes consistently.
"""

from typing import Any, Dict, Optional


class DomainError(Exception):
    """Base exception for all RoboEase domain and infrastructure errors.

    Every subclass must populate `_status_code` so the global exception
    handler can produce the correct HTTP response without a static mapping
    table.
    """

    _status_code: int = 500

    def __init__(
        self,
        message: str = "",
        detail: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message or self.__class__.__name__
        self.detail = detail
        self.context = context or {}

    @property
    def status_code(self) -> int:
        return self._status_code


class ConfigurationError(DomainError):
    """A required configuration key is missing or invalid."""

    _status_code = 500

    def __init__(
        self,
        message: str = "",
        key: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = dict(context or {})
        if key:
            ctx["key"] = key
        super().__init__(message or "Configuration error", context=ctx)
        self.key = key


class NotFoundError(DomainError):
    """A requested resource does not exist."""

    _status_code = 404

    def __init__(
        self,
        entity: str = "",
        entity_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = dict(context or {})
        if entity_id:
            ctx["entity_id"] = entity_id
        msg = f"{entity} not found" if entity else "Resource not found"
        super().__init__(msg, context=ctx)
        self.entity = entity
        self.entity_id = entity_id


class ValidationError(DomainError):
    """Request validation failed (e.g., bad input, missing field)."""

    _status_code = 400


class UnauthorizedError(DomainError):
    """Authentication is required but missing or invalid."""

    _status_code = 401


class ForbiddenError(DomainError):
    """The authenticated user does not have the required permission."""

    _status_code = 403


class ConflictError(DomainError):
    """A resource already exists (e.g., duplicate username)."""

    _status_code = 409


class RepositoryError(DomainError):
    """Generic data-access layer error."""

    _status_code = 500
