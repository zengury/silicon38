"""
Unit tests for common.errors — exception hierarchy.
"""

from common.errors import (
    DomainError,
    NotFoundError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    ConflictError,
    ConfigurationError,
)


class TestDomainErrors:
    """Verify error status codes and context packing."""

    def test_not_found_status_code(self):
        err = NotFoundError(entity="User", entity_id="123")
        assert err.status_code == 404

    def test_not_found_message(self):
        err = NotFoundError(entity="User", entity_id="123")
        assert "User" in str(err)

    def test_validation_error(self):
        err = ValidationError("Bad input", detail="name is required")
        assert err.status_code == 400
        assert err.detail == "name is required"

    def test_unauthorized(self):
        err = UnauthorizedError("Invalid token")
        assert err.status_code == 401

    def test_forbidden(self):
        err = ForbiddenError("Insufficient permissions")
        assert err.status_code == 403

    def test_conflict(self):
        err = ConflictError("Duplicate username")
        assert err.status_code == 409

    def test_configuration_error_with_key(self):
        err = ConfigurationError(key="DATABASE_URL")
        assert err.key == "DATABASE_URL"
        assert err.context == {"key": "DATABASE_URL"}

    def test_default_status_code(self):
        err = DomainError("Generic error")
        assert err.status_code == 500

    def test_context_preservation(self):
        err = NotFoundError(
            entity="Task",
            entity_id="t1",
            context={"tenant": "acme"},
        )
        assert err.context == {"entity_id": "t1", "tenant": "acme"}
