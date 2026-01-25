"""Tests for global exception handlers.

测试说明:
---------
异常处理器现在直接从异常类读取 http_status 属性，无需维护映射表。
测试验证：
1. 异常类的 http_status 属性正确
2. 异常处理器正确读取 http_status 并返回对应状态码
3. 响应格式为统一的 {"error": {"code", "message", "details", "trace_id"}}
"""

import json

import pytest
from fastapi import status
from starlette.requests import Request

from src.shared.api.exception_handlers import (
    domain_exception_handler,
    security_exception_handler,
)
from src.shared.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    ResourceQuotaExceededError,
    ValidationError,
)
from src.shared.infrastructure.security.exceptions import (
    AccountLockedError,
    AuthenticationError,
    InsufficientPermissionsError,
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


class TestDomainExceptionHttpStatus:
    """Test domain exception http_status class attribute."""

    def test_entity_not_found_has_404(self):
        assert EntityNotFoundError.http_status == status.HTTP_404_NOT_FOUND

    def test_duplicate_entity_has_409(self):
        assert DuplicateEntityError.http_status == status.HTTP_409_CONFLICT

    def test_invalid_state_transition_has_409(self):
        assert InvalidStateTransitionError.http_status == status.HTTP_409_CONFLICT

    def test_validation_error_has_422(self):
        assert ValidationError.http_status == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_resource_quota_exceeded_has_429(self):
        assert (
            ResourceQuotaExceededError.http_status == status.HTTP_429_TOO_MANY_REQUESTS
        )

    def test_domain_error_default_400(self):
        assert DomainError.http_status == status.HTTP_400_BAD_REQUEST


class TestSecurityExceptionHttpStatus:
    """Test security exception http_status class attribute."""

    def test_authentication_error_has_401(self):
        assert AuthenticationError.http_status == status.HTTP_401_UNAUTHORIZED

    def test_invalid_credentials_has_401(self):
        assert InvalidCredentialsError.http_status == status.HTTP_401_UNAUTHORIZED

    def test_user_not_found_has_404(self):
        assert UserNotFoundError.http_status == status.HTTP_404_NOT_FOUND

    def test_token_expired_has_401(self):
        assert TokenExpiredError.http_status == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_has_401(self):
        assert InvalidTokenError.http_status == status.HTTP_401_UNAUTHORIZED

    def test_account_locked_has_423(self):
        assert AccountLockedError.http_status == status.HTTP_423_LOCKED

    def test_password_expired_has_401(self):
        assert PasswordExpiredError.http_status == status.HTTP_401_UNAUTHORIZED

    def test_password_too_weak_has_400(self):
        assert PasswordTooWeakError.http_status == status.HTTP_400_BAD_REQUEST

    def test_password_history_violation_has_400(self):
        assert PasswordHistoryViolationError.http_status == status.HTTP_400_BAD_REQUEST

    def test_insufficient_permissions_has_403(self):
        assert InsufficientPermissionsError.http_status == status.HTTP_403_FORBIDDEN

    def test_sso_error_has_401(self):
        assert SSOError.http_status == status.HTTP_401_UNAUTHORIZED

    def test_sso_degraded_mode_has_503(self):
        assert SSODegradedModeError.http_status == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_security_error_default_401(self):
        assert SecurityError.http_status == status.HTTP_401_UNAUTHORIZED


class TestDomainExceptionGetDetails:
    """Test domain exception get_details() method."""

    def test_entity_not_found_details(self):
        exc = EntityNotFoundError("TrainingJob", "123")
        details = exc.get_details()
        assert details == {"entity_type": "TrainingJob", "entity_id": "123"}

    def test_duplicate_entity_details(self):
        exc = DuplicateEntityError("TrainingJob", "test-job")
        details = exc.get_details()
        assert details == {"entity_type": "TrainingJob", "identifier": "test-job"}

    def test_validation_error_details_with_field(self):
        exc = ValidationError("Invalid input", field="name")
        details = exc.get_details()
        assert details == {"field": "name"}

    def test_validation_error_details_without_field(self):
        exc = ValidationError("Invalid input")
        details = exc.get_details()
        assert details is None

    def test_invalid_state_transition_details(self):
        exc = InvalidStateTransitionError("TrainingJob", "running", "submitted")
        details = exc.get_details()
        assert details == {
            "entity_type": "TrainingJob",
            "current_state": "running",
            "target_state": "submitted",
        }

    def test_resource_quota_exceeded_details(self):
        exc = ResourceQuotaExceededError("gpu", 10, 15)
        details = exc.get_details()
        assert details == {"resource_type": "gpu", "limit": 10, "requested": 15}

    def test_base_domain_error_details_none(self):
        exc = DomainError("Unknown error")
        details = exc.get_details()
        assert details is None


class TestDomainExceptionHandler:
    """Test domain_exception_handler function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request without trace_id."""
        scope = {"type": "http", "method": "GET", "path": "/test"}
        return Request(scope)

    @pytest.fixture
    def mock_request_with_trace_id(self):
        """Create a mock request with trace_id."""
        scope = {"type": "http", "method": "GET", "path": "/test"}
        request = Request(scope)
        request.state.trace_id = "test-trace-123"
        return request

    @pytest.mark.asyncio
    async def test_entity_not_found_response_format(self, mock_request):
        """Test unified error response format for EntityNotFoundError."""
        exc = EntityNotFoundError("TrainingJob", "123")
        response = await domain_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        content = json.loads(response.body)

        # 验证统一格式
        assert "error" in content
        assert content["error"]["code"] == "ENTITY_NOT_FOUND"
        assert content["error"]["message"] == "TrainingJob with id '123' not found"
        assert content["error"]["details"] == {
            "entity_type": "TrainingJob",
            "entity_id": "123",
        }

    @pytest.mark.asyncio
    async def test_response_includes_trace_id(self, mock_request_with_trace_id):
        """Test that trace_id is included in response."""
        exc = EntityNotFoundError("TrainingJob", "123")
        response = await domain_exception_handler(mock_request_with_trace_id, exc)

        content = json.loads(response.body)
        assert content["error"]["trace_id"] == "test-trace-123"

    @pytest.mark.asyncio
    async def test_response_without_trace_id(self, mock_request):
        """Test that trace_id is omitted when not available."""
        exc = EntityNotFoundError("TrainingJob", "123")
        response = await domain_exception_handler(mock_request, exc)

        content = json.loads(response.body)
        assert "trace_id" not in content["error"]

    @pytest.mark.asyncio
    async def test_duplicate_entity_response(self, mock_request):
        exc = DuplicateEntityError("TrainingJob", "test-job")
        response = await domain_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_409_CONFLICT
        content = json.loads(response.body)
        assert content["error"]["code"] == "DUPLICATE_ENTITY"
        assert "already exists" in content["error"]["message"]
        assert content["error"]["details"]["entity_type"] == "TrainingJob"

    @pytest.mark.asyncio
    async def test_invalid_state_transition_response(self, mock_request):
        exc = InvalidStateTransitionError("TrainingJob", "running", "submitted")
        response = await domain_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_409_CONFLICT
        content = json.loads(response.body)
        assert content["error"]["code"] == "INVALID_STATE_TRANSITION"
        assert "Cannot transition" in content["error"]["message"]

    @pytest.mark.asyncio
    async def test_unknown_domain_error_returns_400(self, mock_request):
        exc = DomainError("Unknown error")
        response = await domain_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        content = json.loads(response.body)
        assert content["error"]["code"] == "DOMAIN_ERROR"

    @pytest.mark.asyncio
    async def test_validation_error_with_field_details(self, mock_request):
        exc = ValidationError("Invalid input", field="name")
        response = await domain_exception_handler(mock_request, exc)

        content = json.loads(response.body)
        assert content["error"]["code"] == "VALIDATION_ERROR"
        assert content["error"]["details"] == {"field": "name"}

    @pytest.mark.asyncio
    async def test_validation_error_without_field_no_details(self, mock_request):
        exc = ValidationError("Invalid input")
        response = await domain_exception_handler(mock_request, exc)

        content = json.loads(response.body)
        assert content["error"]["code"] == "VALIDATION_ERROR"
        assert "details" not in content["error"]


class TestSecurityExceptionHandler:
    """Test security_exception_handler function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        scope = {"type": "http", "method": "POST", "path": "/auth/login"}
        return Request(scope)

    @pytest.fixture
    def mock_request_with_trace_id(self):
        """Create a mock request with trace_id."""
        scope = {"type": "http", "method": "POST", "path": "/auth/login"}
        request = Request(scope)
        request.state.trace_id = "test-trace-456"
        return request

    @pytest.mark.asyncio
    async def test_authentication_error_response_format(self, mock_request):
        """Test unified error response format for AuthenticationError."""
        exc = AuthenticationError("Invalid credentials")
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        content = json.loads(response.body)

        # 验证统一格式
        assert "error" in content
        assert content["error"]["code"] == "AUTHENTICATION_FAILED"
        assert content["error"]["message"] == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_response_includes_trace_id(self, mock_request_with_trace_id):
        """Test that trace_id is included in response."""
        exc = AuthenticationError("Invalid credentials")
        response = await security_exception_handler(mock_request_with_trace_id, exc)

        content = json.loads(response.body)
        assert content["error"]["trace_id"] == "test-trace-456"

    @pytest.mark.asyncio
    async def test_account_locked_with_until(self, mock_request):
        exc = AccountLockedError("Account locked", locked_until="2024-01-01T12:00:00")
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_423_LOCKED
        content = json.loads(response.body)
        assert content["error"]["code"] == "ACCOUNT_LOCKED"
        assert content["error"]["details"]["locked_until"] == "2024-01-01T12:00:00"

    @pytest.mark.asyncio
    async def test_password_too_weak_includes_violations(self, mock_request):
        violations = ["too short", "no uppercase"]
        exc = PasswordTooWeakError(violations)
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        content = json.loads(response.body)
        assert content["error"]["code"] == "PASSWORD_TOO_WEAK"
        assert content["error"]["details"]["violations"] == violations

    @pytest.mark.asyncio
    async def test_user_not_found_returns_404(self, mock_request):
        exc = UserNotFoundError("user-123")
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        content = json.loads(response.body)
        assert content["error"]["code"] == "USER_NOT_FOUND"
        assert content["error"]["details"]["user_id"] == "user-123"

    @pytest.mark.asyncio
    async def test_unknown_security_error_returns_401(self, mock_request):
        exc = SecurityError("Unknown security error")
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        content = json.loads(response.body)
        assert content["error"]["code"] == "SECURITY_ERROR"

    @pytest.mark.asyncio
    async def test_insufficient_permissions_returns_403(self, mock_request):
        exc = InsufficientPermissionsError("admin")
        response = await security_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        content = json.loads(response.body)
        assert content["error"]["code"] == "INSUFFICIENT_PERMISSIONS"
        assert content["error"]["details"]["required_permission"] == "admin"


class TestTracingMiddleware:
    """Test TracingMiddleware integration with exception handlers."""

    @pytest.fixture
    def mock_request_with_state(self):
        """Create a mock request with state for trace_id."""
        scope = {"type": "http", "method": "GET", "path": "/test"}
        request = Request(scope)
        request.state.trace_id = "abc12345"
        return request

    @pytest.mark.asyncio
    async def test_domain_error_includes_trace_id_from_middleware(
        self, mock_request_with_state
    ):
        """Test that domain exception handler uses trace_id from request state."""
        exc = EntityNotFoundError("Model", "xyz")
        response = await domain_exception_handler(mock_request_with_state, exc)

        content = json.loads(response.body)
        assert content["error"]["trace_id"] == "abc12345"

    @pytest.mark.asyncio
    async def test_security_error_includes_trace_id_from_middleware(
        self, mock_request_with_state
    ):
        """Test that security exception handler uses trace_id from request state."""
        exc = InvalidCredentialsError()
        response = await security_exception_handler(mock_request_with_state, exc)

        content = json.loads(response.body)
        assert content["error"]["trace_id"] == "abc12345"
