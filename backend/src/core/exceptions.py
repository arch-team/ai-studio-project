"""Unified exception handling module.

Provides a consistent exception hierarchy for the entire application,
improving error handling and enabling better error classification.

Features:
- Hierarchical exception classes with built-in HTTP status codes
- Automatic HTTP status code via http_status class attribute
- Standard error structure with message, code, and details
"""

from http import HTTPStatus
from typing import ClassVar, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Future type imports if needed


class AppException(Exception):
    """Base exception for all application errors.

    All custom exceptions should inherit from this class to enable
    unified exception handling and error classification.

    Subclasses can override http_status to specify their HTTP status code.
    """

    # 默认 HTTP 状态码，子类可覆盖
    http_status: ClassVar[int] = HTTPStatus.INTERNAL_SERVER_ERROR

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

    http_status: ClassVar[int] = HTTPStatus.UNAUTHORIZED


class AuthorizationError(AppException):
    """Raised when user lacks permission for an action."""

    http_status: ClassVar[int] = HTTPStatus.FORBIDDEN


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""

    pass  # 继承 401 UNAUTHORIZED


class AccountLockedError(AuthenticationError):
    """Raised when account is locked due to failed login attempts."""

    http_status: ClassVar[int] = HTTPStatus.TOO_MANY_REQUESTS  # 429


class AccountDisabledError(AuthenticationError):
    """Raised when account is disabled."""

    http_status: ClassVar[int] = HTTPStatus.FORBIDDEN  # 403


class PasswordExpiredError(AuthenticationError):
    """Raised when password has expired."""

    pass  # 继承 401 UNAUTHORIZED


class TokenError(AuthenticationError):
    """Raised for token-related errors (invalid, expired, etc.)."""

    pass  # 继承 401 UNAUTHORIZED


# Resource Exceptions
class ResourceNotFoundError(AppException):
    """Raised when a requested resource is not found."""

    http_status: ClassVar[int] = HTTPStatus.NOT_FOUND


class ResourceConflictError(AppException):
    """Raised when a resource conflict occurs (e.g., duplicate)."""

    http_status: ClassVar[int] = HTTPStatus.CONFLICT


class ResourceValidationError(AppException):
    """Raised when resource validation fails."""

    http_status: ClassVar[int] = HTTPStatus.BAD_REQUEST


# S3/Storage Exceptions
class StorageError(AppException):
    """Base exception for storage operations."""

    pass  # 继承 500 INTERNAL_SERVER_ERROR


class S3Error(StorageError):
    """Base exception for S3 operations."""

    pass  # 继承 500 INTERNAL_SERVER_ERROR


class S3NotFoundError(S3Error):
    """Raised when S3 object is not found."""

    http_status: ClassVar[int] = HTTPStatus.NOT_FOUND


class S3PermissionError(S3Error):
    """Raised when S3 permission is denied."""

    http_status: ClassVar[int] = HTTPStatus.FORBIDDEN


class S3UploadError(S3Error):
    """Raised when S3 upload fails."""

    pass  # 继承 500 INTERNAL_SERVER_ERROR


class S3DownloadError(S3Error):
    """Raised when S3 download fails."""

    pass  # 继承 500 INTERNAL_SERVER_ERROR


class S3DeleteError(S3Error):
    """Raised when S3 delete fails."""

    pass  # 继承 500 INTERNAL_SERVER_ERROR


# Validation Exceptions
class ValidationError(AppException):
    """Raised when input validation fails."""

    http_status: ClassVar[int] = HTTPStatus.BAD_REQUEST


class PasswordValidationError(ValidationError):
    """Raised when password doesn't meet policy requirements."""

    pass  # 继承 400 BAD_REQUEST


class PasswordHistoryError(ValidationError):
    """Raised when new password matches a recent password."""

    pass  # 继承 400 BAD_REQUEST


class PasswordResetTokenError(ValidationError):
    """Raised when password reset token is invalid or expired.

    Distinct from TokenError to use 400 status instead of 401,
    as password reset is a validation scenario, not authentication.
    """

    pass  # 继承 400 BAD_REQUEST


# Service Exceptions
class ServiceUnavailableError(AppException):
    """Raised when an external service is unavailable."""

    http_status: ClassVar[int] = HTTPStatus.SERVICE_UNAVAILABLE


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing."""

    http_status: ClassVar[int] = HTTPStatus.SERVICE_UNAVAILABLE


# SSO Exceptions
class SSOError(AppException):
    """Base exception for SSO operations."""

    http_status: ClassVar[int] = HTTPStatus.BAD_GATEWAY


class SSOConfigurationError(SSOError):
    """Raised when SSO configuration is missing or invalid."""

    http_status: ClassVar[int] = HTTPStatus.SERVICE_UNAVAILABLE


class SSODiscoveryError(SSOError):
    """Raised when OIDC discovery fails."""

    pass  # 继承 502 BAD_GATEWAY


class SSOTokenExchangeError(SSOError):
    """Raised when token exchange fails."""

    pass  # 继承 502 BAD_GATEWAY


class SSOUserInfoError(SSOError):
    """Raised when userinfo request fails."""

    pass  # 继承 502 BAD_GATEWAY


class SSOTokenVerificationError(SSOError):
    """Raised when ID token verification fails."""

    pass  # 继承 502 BAD_GATEWAY


# HyperPod Exceptions
class HyperPodError(AppException):
    """Base exception for HyperPod operations."""

    pass  # 继承 500 INTERNAL_SERVER_ERROR


class HyperPodSDKNotAvailableError(HyperPodError):
    """Raised when HyperPod SDK is not installed."""

    http_status: ClassVar[int] = HTTPStatus.SERVICE_UNAVAILABLE


class HyperPodJobCreationError(HyperPodError):
    """Raised when training job creation fails."""

    pass  # 继承 500 INTERNAL_SERVER_ERROR


class HyperPodJobNotFoundError(HyperPodError):
    """Raised when training job is not found."""

    http_status: ClassVar[int] = HTTPStatus.NOT_FOUND


class HyperPodJobDeletionError(HyperPodError):
    """Raised when training job deletion fails."""

    pass  # 继承 500 INTERNAL_SERVER_ERROR


def get_http_status_code(exc: AppException) -> int:
    """Get HTTP status code for an exception.

    Uses the http_status class attribute defined on the exception class.
    Falls back to 500 Internal Server Error if no attribute is found.

    Args:
        exc: Application exception instance

    Returns:
        HTTP status code as integer
    """
    return getattr(exc, "http_status", HTTPStatus.INTERNAL_SERVER_ERROR)
