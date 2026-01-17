"""Tests for global exception handlers."""

import pytest
from fastapi import status
from starlette.requests import Request
from starlette.testclient import TestClient

from src.shared.api.exception_handlers import (
    DOMAIN_EXCEPTION_MAP,
    SECURITY_EXCEPTION_MAP,
    domain_exception_handler,
    security_exception_handler,
)
from src.shared.infrastructure.security.exceptions import (
    AccountLockedError,
    AuthenticationError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordExpiredError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
    SecurityError,
    SSODegradedModeError,
    SSOError,
    TokenExpiredError,
    UserNotFoundError,
)
from src.shared.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    ResourceQuotaExceededError,
    ValidationError,
)


class TestDomainExceptionMap:
    """Test domain exception to HTTP status code mapping."""

    def test_entity_not_found_maps_to_404(self):
        assert DOMAIN_EXCEPTION_MAP[EntityNotFoundError] == status.HTTP_404_NOT_FOUND

    def test_duplicate_entity_maps_to_409(self):
        assert DOMAIN_EXCEPTION_MAP[DuplicateEntityError] == status.HTTP_409_CONFLICT

    def test_invalid_state_transition_maps_to_409(self):
        assert (
            DOMAIN_EXCEPTION_MAP[InvalidStateTransitionError]
            == status.HTTP_409_CONFLICT
        )

    def test_validation_error_maps_to_422(self):
        assert (
            DOMAIN_EXCEPTION_MAP[ValidationError]
            == status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    def test_resource_quota_exceeded_maps_to_429(self):
        assert (
            DOMAIN_EXCEPTION_MAP[ResourceQuotaExceededError]
            == status.HTTP_429_TOO_MANY_REQUESTS
        )


class TestSecurityExceptionMap:
    """Test security exception to HTTP status code mapping."""

    def test_authentication_error_maps_to_401(self):
        assert (
            SECURITY_EXCEPTION_MAP[AuthenticationError]
            == status.HTTP_401_UNAUTHORIZED
        )

    def test_invalid_credentials_maps_to_401(self):
        assert (
            SECURITY_EXCEPTION_MAP[InvalidCredentialsError]
            == status.HTTP_401_UNAUTHORIZED
        )

    def test_user_not_found_maps_to_404(self):
        assert SECURITY_EXCEPTION_MAP[UserNotFoundError] == status.HTTP_404_NOT_FOUND

    def test_token_expired_maps_to_401(self):
        assert SECURITY_EXCEPTION_MAP[TokenExpiredError] == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_maps_to_401(self):
        assert SECURITY_EXCEPTION_MAP[InvalidTokenError] == status.HTTP_401_UNAUTHORIZED

    def test_account_locked_maps_to_423(self):
        assert SECURITY_EXCEPTION_MAP[AccountLockedError] == status.HTTP_423_LOCKED

    def test_password_expired_maps_to_401(self):
        assert (
            SECURITY_EXCEPTION_MAP[PasswordExpiredError]
            == status.HTTP_401_UNAUTHORIZED
        )

    def test_password_too_weak_maps_to_400(self):
        assert (
            SECURITY_EXCEPTION_MAP[PasswordTooWeakError] == status.HTTP_400_BAD_REQUEST
        )

    def test_password_history_violation_maps_to_400(self):
        assert (
            SECURITY_EXCEPTION_MAP[PasswordHistoryViolationError]
            == status.HTTP_400_BAD_REQUEST
        )

    def test_sso_error_maps_to_401(self):
        assert SECURITY_EXCEPTION_MAP[SSOError] == status.HTTP_401_UNAUTHORIZED

    def test_sso_degraded_mode_maps_to_503(self):
        assert (
            SECURITY_EXCEPTION_MAP[SSODegradedModeError]
            == status.HTTP_503_SERVICE_UNAVAILABLE
        )


class TestDomainExceptionHandler:
    """Test domain_exception_handler function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        scope = {"type": "http", "method": "GET", "path": "/test"}
        return Request(scope)

    @pytest.mark.asyncio
    async def test_entity_not_found_response(self, mock_request):
        exc = EntityNotFoundError("TrainingJob", "123")
        response = await domain_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert b"TrainingJob with id '123' not found" in response.body
        assert b"EntityNotFoundError" in response.body

    @pytest.mark.asyncio
    async def test_duplicate_entity_response(self, mock_request):
        exc = DuplicateEntityError("TrainingJob", "test-job")
        response = await domain_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert b"already exists" in response.body
        assert b"DuplicateEntityError" in response.body

    @pytest.mark.asyncio
    async def test_invalid_state_transition_response(self, mock_request):
        exc = InvalidStateTransitionError("TrainingJob", "running", "submitted")
        response = await domain_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert b"Cannot transition" in response.body

    @pytest.mark.asyncio
    async def test_unknown_domain_error_returns_400(self, mock_request):
        exc = DomainError("Unknown error")
        response = await domain_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestSecurityExceptionHandler:
    """Test security_exception_handler function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        scope = {"type": "http", "method": "POST", "path": "/auth/login"}
        return Request(scope)

    @pytest.mark.asyncio
    async def test_authentication_error_response(self, mock_request):
        exc = AuthenticationError("Invalid credentials")
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert b"Invalid credentials" in response.body
        assert b"AUTHENTICATION_FAILED" in response.body

    @pytest.mark.asyncio
    async def test_account_locked_with_until(self, mock_request):
        exc = AccountLockedError("Account locked", locked_until="2024-01-01T12:00:00")
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_423_LOCKED
        assert b"2024-01-01T12:00:00" in response.body

    @pytest.mark.asyncio
    async def test_password_too_weak_includes_violations(self, mock_request):
        violations = ["too short", "no uppercase"]
        exc = PasswordTooWeakError(violations)
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert b"too short" in response.body
        assert b"no uppercase" in response.body

    @pytest.mark.asyncio
    async def test_user_not_found_returns_404(self, mock_request):
        exc = UserNotFoundError("user-123")
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert b"user-123" in response.body

    @pytest.mark.asyncio
    async def test_unknown_security_error_returns_401(self, mock_request):
        exc = SecurityError("Unknown security error")
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
