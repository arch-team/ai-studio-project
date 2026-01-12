"""Test exception definitions and HTTP status code mapping."""

import pytest
from http import HTTPStatus

from src.core.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    InvalidCredentialsError,
    AccountLockedError,
    AccountDisabledError,
    PasswordExpiredError,
    TokenError,
    ResourceNotFoundError,
    ResourceConflictError,
    ResourceValidationError,
    StorageError,
    S3Error,
    S3NotFoundError,
    S3PermissionError,
    S3UploadError,
    S3DownloadError,
    S3DeleteError,
    ValidationError,
    PasswordValidationError,
    PasswordHistoryError,
    PasswordResetTokenError,
    ServiceUnavailableError,
    ConfigurationError,
    SSOError,
    SSOConfigurationError,
    SSODiscoveryError,
    SSOTokenExchangeError,
    SSOUserInfoError,
    SSOTokenVerificationError,
    HyperPodError,
    HyperPodSDKNotAvailableError,
    HyperPodJobCreationError,
    HyperPodJobNotFoundError,
    HyperPodJobDeletionError,
    get_http_status_code,
)


class TestAppException:
    """Test AppException base class."""

    def test_init_with_message_only(self):
        """Test exception with message only."""
        exc = AppException("Test error")
        assert exc.message == "Test error"
        assert exc.code == "AppException"
        assert exc.details == {}
        assert str(exc) == "Test error"

    def test_init_with_all_params(self):
        """Test exception with all parameters."""
        exc = AppException(
            message="Test error",
            code="TEST_ERROR",
            details={"key": "value"},
        )
        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert exc.details == {"key": "value"}

    def test_subclass_inherits_code_from_class_name(self):
        """Test that subclass uses its class name as default code."""
        exc = ResourceNotFoundError("Not found")
        assert exc.code == "ResourceNotFoundError"

    def test_subclass_can_override_code(self):
        """Test that subclass can override default code."""
        exc = ResourceNotFoundError("Not found", code="CUSTOM_CODE")
        assert exc.code == "CUSTOM_CODE"


class TestHTTPStatusMapping:
    """Test http_status class attribute coverage and correctness."""

    @pytest.mark.parametrize(
        "exc_class,expected_status",
        [
            # 400 Bad Request
            (ValidationError, HTTPStatus.BAD_REQUEST),
            (PasswordValidationError, HTTPStatus.BAD_REQUEST),
            (PasswordHistoryError, HTTPStatus.BAD_REQUEST),
            (PasswordResetTokenError, HTTPStatus.BAD_REQUEST),
            (ResourceValidationError, HTTPStatus.BAD_REQUEST),
            # 401 Unauthorized
            (AuthenticationError, HTTPStatus.UNAUTHORIZED),
            (InvalidCredentialsError, HTTPStatus.UNAUTHORIZED),
            (TokenError, HTTPStatus.UNAUTHORIZED),
            (PasswordExpiredError, HTTPStatus.UNAUTHORIZED),
            # 403 Forbidden
            (AuthorizationError, HTTPStatus.FORBIDDEN),
            (AccountDisabledError, HTTPStatus.FORBIDDEN),
            (S3PermissionError, HTTPStatus.FORBIDDEN),
            # 404 Not Found
            (ResourceNotFoundError, HTTPStatus.NOT_FOUND),
            (S3NotFoundError, HTTPStatus.NOT_FOUND),
            (HyperPodJobNotFoundError, HTTPStatus.NOT_FOUND),
            # 409 Conflict
            (ResourceConflictError, HTTPStatus.CONFLICT),
            # 429 Too Many Requests
            (AccountLockedError, HTTPStatus.TOO_MANY_REQUESTS),
            # 500 Internal Server Error
            (StorageError, HTTPStatus.INTERNAL_SERVER_ERROR),
            (S3Error, HTTPStatus.INTERNAL_SERVER_ERROR),
            (S3UploadError, HTTPStatus.INTERNAL_SERVER_ERROR),
            (S3DownloadError, HTTPStatus.INTERNAL_SERVER_ERROR),
            (S3DeleteError, HTTPStatus.INTERNAL_SERVER_ERROR),
            (HyperPodError, HTTPStatus.INTERNAL_SERVER_ERROR),
            (HyperPodJobCreationError, HTTPStatus.INTERNAL_SERVER_ERROR),
            (HyperPodJobDeletionError, HTTPStatus.INTERNAL_SERVER_ERROR),
            # 502 Bad Gateway
            (SSOError, HTTPStatus.BAD_GATEWAY),
            (SSODiscoveryError, HTTPStatus.BAD_GATEWAY),
            (SSOTokenExchangeError, HTTPStatus.BAD_GATEWAY),
            (SSOUserInfoError, HTTPStatus.BAD_GATEWAY),
            (SSOTokenVerificationError, HTTPStatus.BAD_GATEWAY),
            # 503 Service Unavailable
            (ServiceUnavailableError, HTTPStatus.SERVICE_UNAVAILABLE),
            (SSOConfigurationError, HTTPStatus.SERVICE_UNAVAILABLE),
            (HyperPodSDKNotAvailableError, HTTPStatus.SERVICE_UNAVAILABLE),
            (ConfigurationError, HTTPStatus.SERVICE_UNAVAILABLE),
        ],
    )
    def test_status_mapping_via_http_status_attr(self, exc_class, expected_status):
        """Test that each exception class has correct http_status attribute."""
        assert hasattr(exc_class, "http_status")
        assert exc_class.http_status == expected_status


class TestGetHttpStatusCode:
    """Test get_http_status_code function."""

    def test_direct_mapping(self):
        """Test direct exception type mapping."""
        exc = ResourceNotFoundError("Not found")
        assert get_http_status_code(exc) == HTTPStatus.NOT_FOUND

    def test_inheritance_mapping_uses_mro(self):
        """Test that MRO is used for inherited exceptions."""
        # PasswordHistoryError -> ValidationError -> AppException
        exc = PasswordHistoryError("Password in history")
        status = get_http_status_code(exc)
        # Should find PasswordHistoryError first (400)
        assert status == HTTPStatus.BAD_REQUEST

    def test_fallback_to_parent_mapping(self):
        """Test fallback to parent class mapping when child not mapped."""

        # Create an unmapped subclass dynamically
        class CustomAuthError(AuthenticationError):
            pass

        exc = CustomAuthError("Custom auth error")
        # Should fall back to AuthenticationError mapping (401)
        assert get_http_status_code(exc) == HTTPStatus.UNAUTHORIZED

    def test_sso_error_hierarchy(self):
        """Test SSO error hierarchy mapping."""
        # SSODiscoveryError -> SSOError -> AppException
        exc = SSODiscoveryError("Discovery failed")
        # Should find SSODiscoveryError (502)
        assert get_http_status_code(exc) == HTTPStatus.BAD_GATEWAY

    def test_hyperpod_error_hierarchy(self):
        """Test HyperPod error hierarchy mapping."""
        exc = HyperPodJobNotFoundError("Job not found")
        # Should find HyperPodJobNotFoundError (404)
        assert get_http_status_code(exc) == HTTPStatus.NOT_FOUND

    def test_s3_error_hierarchy(self):
        """Test S3 error hierarchy mapping."""
        exc = S3UploadError("Upload failed")
        # Should find S3UploadError (500)
        assert get_http_status_code(exc) == HTTPStatus.INTERNAL_SERVER_ERROR


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_app_exception(self):
        """Test that all custom exceptions inherit from AppException."""
        exception_classes = [
            AuthenticationError,
            AuthorizationError,
            InvalidCredentialsError,
            AccountLockedError,
            AccountDisabledError,
            PasswordExpiredError,
            TokenError,
            ResourceNotFoundError,
            ResourceConflictError,
            ResourceValidationError,
            StorageError,
            S3Error,
            ValidationError,
            PasswordValidationError,
            PasswordHistoryError,
            ServiceUnavailableError,
            ConfigurationError,
            SSOError,
            HyperPodError,
        ]
        for exc_class in exception_classes:
            assert issubclass(
                exc_class, AppException
            ), f"{exc_class.__name__} should inherit from AppException"

    def test_authentication_hierarchy(self):
        """Test authentication exception hierarchy."""
        assert issubclass(InvalidCredentialsError, AuthenticationError)
        assert issubclass(TokenError, AuthenticationError)
        assert issubclass(PasswordExpiredError, AuthenticationError)
        assert issubclass(AccountLockedError, AuthenticationError)
        assert issubclass(AccountDisabledError, AuthenticationError)

    def test_validation_hierarchy(self):
        """Test validation exception hierarchy."""
        assert issubclass(PasswordValidationError, ValidationError)
        assert issubclass(PasswordHistoryError, ValidationError)
        assert issubclass(PasswordResetTokenError, ValidationError)

    def test_storage_hierarchy(self):
        """Test storage exception hierarchy."""
        assert issubclass(S3Error, StorageError)
        assert issubclass(S3NotFoundError, S3Error)
        assert issubclass(S3PermissionError, S3Error)
        assert issubclass(S3UploadError, S3Error)
        assert issubclass(S3DownloadError, S3Error)
        assert issubclass(S3DeleteError, S3Error)

    def test_sso_hierarchy(self):
        """Test SSO exception hierarchy."""
        assert issubclass(SSOConfigurationError, SSOError)
        assert issubclass(SSODiscoveryError, SSOError)
        assert issubclass(SSOTokenExchangeError, SSOError)
        assert issubclass(SSOUserInfoError, SSOError)
        assert issubclass(SSOTokenVerificationError, SSOError)

    def test_hyperpod_hierarchy(self):
        """Test HyperPod exception hierarchy."""
        assert issubclass(HyperPodSDKNotAvailableError, HyperPodError)
        assert issubclass(HyperPodJobCreationError, HyperPodError)
        assert issubclass(HyperPodJobNotFoundError, HyperPodError)
        assert issubclass(HyperPodJobDeletionError, HyperPodError)


class TestExceptionDetails:
    """Test exception details functionality."""

    def test_details_preserved(self):
        """Test that details are preserved correctly."""
        details = {"username": "test_user", "email": "test@example.com"}
        exc = ResourceConflictError(
            message="Account already exists",
            code="ACCOUNT_EXISTS",
            details=details,
        )
        assert exc.details == details
        assert exc.details["username"] == "test_user"

    def test_details_default_to_empty_dict(self):
        """Test that details default to empty dict."""
        exc = ResourceNotFoundError("Not found")
        assert exc.details == {}
        assert isinstance(exc.details, dict)

    def test_details_mutable(self):
        """Test that details can be modified after creation."""
        exc = ResourceNotFoundError("Not found")
        exc.details["added_key"] = "added_value"
        assert exc.details["added_key"] == "added_value"
