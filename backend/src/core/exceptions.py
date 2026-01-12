"""Unified exception handling module.

Provides a consistent exception hierarchy for the entire application,
improving error handling and enabling better error classification.

Features:
- Hierarchical exception classes for different error domains
- Automatic HTTP status code mapping via get_http_status_code()
- Standard error structure with message, code, and details
"""

from http import HTTPStatus
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Future type imports if needed


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


class PasswordResetTokenError(ValidationError):
    """Raised when password reset token is invalid or expired.

    Distinct from TokenError to use 400 status instead of 401,
    as password reset is a validation scenario, not authentication.
    """

    pass


# Service Exceptions
class ServiceUnavailableError(AppException):
    """Raised when an external service is unavailable."""

    pass


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing."""

    pass


# SSO Exceptions
class SSOError(AppException):
    """Base exception for SSO operations."""

    pass


class SSOConfigurationError(SSOError):
    """Raised when SSO configuration is missing or invalid."""

    pass


class SSODiscoveryError(SSOError):
    """Raised when OIDC discovery fails."""

    pass


class SSOTokenExchangeError(SSOError):
    """Raised when token exchange fails."""

    pass


class SSOUserInfoError(SSOError):
    """Raised when userinfo request fails."""

    pass


class SSOTokenVerificationError(SSOError):
    """Raised when ID token verification fails."""

    pass


# HyperPod Exceptions
class HyperPodError(AppException):
    """Base exception for HyperPod operations."""

    pass


class HyperPodSDKNotAvailableError(HyperPodError):
    """Raised when HyperPod SDK is not installed."""

    pass


class HyperPodJobCreationError(HyperPodError):
    """Raised when training job creation fails."""

    pass


class HyperPodJobNotFoundError(HyperPodError):
    """Raised when training job is not found."""

    pass


class HyperPodJobDeletionError(HyperPodError):
    """Raised when training job deletion fails."""

    pass


# HTTP Status Code Mapping
# Maps exception types to HTTP status codes using Method Resolution Order (MRO)
HTTP_STATUS_MAPPING: dict[type, int] = {
    # 400 Bad Request - Validation errors
    ValidationError: HTTPStatus.BAD_REQUEST,
    PasswordValidationError: HTTPStatus.BAD_REQUEST,
    PasswordHistoryError: HTTPStatus.BAD_REQUEST,
    PasswordResetTokenError: HTTPStatus.BAD_REQUEST,
    ResourceValidationError: HTTPStatus.BAD_REQUEST,
    # 401 Unauthorized - Authentication errors
    AuthenticationError: HTTPStatus.UNAUTHORIZED,
    InvalidCredentialsError: HTTPStatus.UNAUTHORIZED,
    TokenError: HTTPStatus.UNAUTHORIZED,
    PasswordExpiredError: HTTPStatus.UNAUTHORIZED,
    # 403 Forbidden - Authorization errors
    AuthorizationError: HTTPStatus.FORBIDDEN,
    AccountDisabledError: HTTPStatus.FORBIDDEN,
    S3PermissionError: HTTPStatus.FORBIDDEN,
    # 404 Not Found - Resource not found errors
    ResourceNotFoundError: HTTPStatus.NOT_FOUND,
    S3NotFoundError: HTTPStatus.NOT_FOUND,
    HyperPodJobNotFoundError: HTTPStatus.NOT_FOUND,
    # 409 Conflict - Resource conflict errors
    ResourceConflictError: HTTPStatus.CONFLICT,
    # 429 Too Many Requests - Rate limiting
    AccountLockedError: HTTPStatus.TOO_MANY_REQUESTS,
    # 500 Internal Server Error - Server-side errors
    StorageError: HTTPStatus.INTERNAL_SERVER_ERROR,
    S3Error: HTTPStatus.INTERNAL_SERVER_ERROR,
    S3UploadError: HTTPStatus.INTERNAL_SERVER_ERROR,
    S3DownloadError: HTTPStatus.INTERNAL_SERVER_ERROR,
    S3DeleteError: HTTPStatus.INTERNAL_SERVER_ERROR,
    HyperPodError: HTTPStatus.INTERNAL_SERVER_ERROR,
    HyperPodJobCreationError: HTTPStatus.INTERNAL_SERVER_ERROR,
    HyperPodJobDeletionError: HTTPStatus.INTERNAL_SERVER_ERROR,
    # 502 Bad Gateway - External service errors
    SSOError: HTTPStatus.BAD_GATEWAY,
    SSODiscoveryError: HTTPStatus.BAD_GATEWAY,
    SSOTokenExchangeError: HTTPStatus.BAD_GATEWAY,
    SSOUserInfoError: HTTPStatus.BAD_GATEWAY,
    SSOTokenVerificationError: HTTPStatus.BAD_GATEWAY,
    # 503 Service Unavailable - Service configuration errors
    ServiceUnavailableError: HTTPStatus.SERVICE_UNAVAILABLE,
    SSOConfigurationError: HTTPStatus.SERVICE_UNAVAILABLE,
    HyperPodSDKNotAvailableError: HTTPStatus.SERVICE_UNAVAILABLE,
    ConfigurationError: HTTPStatus.SERVICE_UNAVAILABLE,
}


def get_http_status_code(exc: AppException) -> int:
    """Get HTTP status code for an exception.

    Uses Method Resolution Order (MRO) to find the most specific mapping.
    Falls back to 500 Internal Server Error if no mapping is found.

    Args:
        exc: Application exception instance

    Returns:
        HTTP status code as integer
    """
    for exc_type in type(exc).__mro__:
        if exc_type in HTTP_STATUS_MAPPING:
            return HTTP_STATUS_MAPPING[exc_type]
    return HTTPStatus.INTERNAL_SERVER_ERROR
