"""Application domain exception hierarchy and RFC 7807 problem details.

Ensures predictable, standard error representations across all endpoints.
"""

from typing import Any

from fastapi import status


class AppException(Exception):
    """Base exception for all domain and application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        resource: str,
        identifier: Any,
        details: dict[str, Any] | None = None,
    ):
        message = f"{resource} with identifier '{identifier}' was not found."
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier), **(details or {})},
        )


class ConflictError(AppException):
    """Raised when a resource state conflicts (e.g. unique constraint violation)."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            code="RESOURCE_CONFLICT",
            details=details,
        )


class UnauthorizedError(AppException):
    """Raised when authentication credentials are missing, invalid or expired."""

    def __init__(self, message: str = "Authentication credentials were invalid or expired."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
        )


class ForbiddenError(AppException):
    """Raised when the authenticated actor lacks permissions for the action."""

    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN_ACCESS",
        )


class ValidationError(AppException):
    """Raised when domain business rules fail validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="DOMAIN_VALIDATION_ERROR",
            details=details,
        )


class InvalidStateTransitionError(ValidationError):
    """Raised when attempting an impossible state transition in a workflow."""

    def __init__(self, current_state: str, target_state: str, reason: str = ""):
        msg = f"Cannot transition from '{current_state}' to '{target_state}'."
        if reason:
            msg += f" {reason}"
        super().__init__(
            message=msg,
            details={"current_state": current_state, "target_state": target_state},
        )
