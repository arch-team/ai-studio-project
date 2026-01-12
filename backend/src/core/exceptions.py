"""Unified exception handling module.

Provides a consistent exception hierarchy for the entire application,
improving error handling and enabling better error classification.
"""

from typing import Optional


class AppException(Exception):
    """Base exception for all application errors.

    All custom exceptions should inherit from this class to enable
    unified exception handling and error classification.
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """Initialize application exception.

        Args:
            message: Human-readable error message
            code: Optional error code for programmatic handling
            details: Optional additional details about the error
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}


# Authentication & Authorization Exceptions
class AuthenticationError(AppException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(AppException):
    """Raised when user lacks permission for an action."""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    pass


class AccountLockedError(AuthenticationError):
    """Raised when account is locked due to failed login attempts."""

    pass


class AccountDisabledError(AuthenticationError):
    """Raised when account is disabled."""

    pass


class PasswordExpiredError(AuthenticationError):
    """Raised when password has expired."""

    pass


class TokenError(AuthenticationError):
    """Raised for token-related errors (invalid, expired, etc.)."""

    pass


# Resource Exceptions
class ResourceNotFoundError(AppException):
    """Raised when a requested resource is not found."""

    pass


class ResourceConflictError(AppException):
    """Raised when a resource conflict occurs (e.g., duplicate)."""

    pass


class ResourceValidationError(AppException):
    """Raised when resource validation fails."""

    pass


# S3/Storage Exceptions
class StorageError(AppException):
    """Base exception for storage operations."""

    pass


class S3Error(StorageError):
    """Base exception for S3 operations."""

    pass


class S3NotFoundError(S3Error):
    """Raised when S3 object is not found."""

    pass


class S3PermissionError(S3Error):
    """Raised when S3 permission is denied."""

    pass


class S3UploadError(S3Error):
    """Raised when S3 upload fails."""

    pass


class S3DownloadError(S3Error):
    """Raised when S3 download fails."""

    pass


class S3DeleteError(S3Error):
    """Raised when S3 delete fails."""

    pass


# Validation Exceptions
class ValidationError(AppException):
    """Raised when input validation fails."""

    pass


class PasswordValidationError(ValidationError):
    """Raised when password doesn't meet policy requirements."""

    pass


class PasswordHistoryError(ValidationError):
    """Raised when new password matches a recent password."""

    pass


# Service Exceptions
class ServiceUnavailableError(AppException):
    """Raised when an external service is unavailable."""

    pass


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing."""

    pass
