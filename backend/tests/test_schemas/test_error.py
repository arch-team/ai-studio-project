"""Test error response schemas."""

import pytest
from datetime import datetime

from src.schemas.error import ErrorDetail, ErrorResponse, ValidationErrorResponse


class TestErrorDetail:
    """Test ErrorDetail schema."""

    def test_create_with_all_fields(self):
        """Test creating ErrorDetail with all fields."""
        detail = ErrorDetail(
            field="username",
            message="Field is required",
            code="missing_field",
        )
        assert detail.field == "username"
        assert detail.message == "Field is required"
        assert detail.code == "missing_field"

    def test_create_with_message_only(self):
        """Test creating ErrorDetail with message only."""
        detail = ErrorDetail(message="An error occurred")
        assert detail.field is None
        assert detail.message == "An error occurred"
        assert detail.code is None

    def test_model_dump(self):
        """Test serialization to dict."""
        detail = ErrorDetail(
            field="email",
            message="Invalid email format",
            code="invalid_email",
        )
        data = detail.model_dump()
        assert data["field"] == "email"
        assert data["message"] == "Invalid email format"
        assert data["code"] == "invalid_email"


class TestErrorResponse:
    """Test ErrorResponse schema."""

    def test_create_with_required_fields(self):
        """Test creating ErrorResponse with required fields only."""
        response = ErrorResponse(
            error="ResourceNotFoundError",
            message="Account not found",
            code="ACCOUNT_NOT_FOUND",
        )
        assert response.error == "ResourceNotFoundError"
        assert response.message == "Account not found"
        assert response.code == "ACCOUNT_NOT_FOUND"
        assert response.details == {}
        assert response.request_id is None
        assert isinstance(response.timestamp, datetime)
        assert response.path is None

    def test_create_with_all_fields(self):
        """Test creating ErrorResponse with all fields."""
        response = ErrorResponse(
            error="ResourceNotFoundError",
            message="Account not found",
            code="ACCOUNT_NOT_FOUND",
            details={"username": "john_doe"},
            request_id="test-request-id",
            path="/api/v1/auth/accounts/john_doe",
        )
        assert response.details == {"username": "john_doe"}
        assert response.request_id == "test-request-id"
        assert response.path == "/api/v1/auth/accounts/john_doe"

    def test_json_serialization(self):
        """Test JSON serialization."""
        response = ErrorResponse(
            error="TestError",
            message="Test message",
            code="TEST",
        )
        json_data = response.model_dump(mode="json")
        assert isinstance(json_data, dict)
        assert "error" in json_data
        assert "message" in json_data
        assert "code" in json_data
        assert "timestamp" in json_data
        # Timestamp should be serialized as string
        assert isinstance(json_data["timestamp"], str)

    def test_details_default_empty_dict(self):
        """Test that details defaults to empty dict."""
        response = ErrorResponse(
            error="TestError",
            message="Test message",
            code="TEST",
        )
        assert response.details == {}
        assert isinstance(response.details, dict)

    def test_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated."""
        before = datetime.utcnow()
        response = ErrorResponse(
            error="TestError",
            message="Test message",
            code="TEST",
        )
        after = datetime.utcnow()
        assert before <= response.timestamp <= after

    def test_custom_timestamp(self):
        """Test that custom timestamp can be provided."""
        custom_time = datetime(2024, 1, 15, 10, 30, 0)
        response = ErrorResponse(
            error="TestError",
            message="Test message",
            code="TEST",
            timestamp=custom_time,
        )
        assert response.timestamp == custom_time


class TestValidationErrorResponse:
    """Test ValidationErrorResponse schema."""

    def test_inherits_from_error_response(self):
        """Test ValidationErrorResponse inherits from ErrorResponse."""
        assert issubclass(ValidationErrorResponse, ErrorResponse)

    def test_create_with_errors_list(self):
        """Test creating with list of ErrorDetail."""
        errors = [
            ErrorDetail(field="username", message="Required", code="missing"),
            ErrorDetail(field="password", message="Too short", code="too_short"),
        ]
        response = ValidationErrorResponse(
            error="ValidationError",
            message="Validation failed",
            code="VALIDATION_ERROR",
            errors=errors,
        )
        assert len(response.errors) == 2
        assert response.errors[0].field == "username"
        assert response.errors[1].field == "password"

    def test_empty_errors_by_default(self):
        """Test that errors list is empty by default."""
        response = ValidationErrorResponse(
            error="ValidationError",
            message="Validation failed",
            code="VALIDATION_ERROR",
        )
        assert response.errors == []

    def test_inherits_all_base_fields(self):
        """Test that all base fields are available."""
        response = ValidationErrorResponse(
            error="ValidationError",
            message="Validation failed",
            code="VALIDATION_ERROR",
            details={"count": 2},
            request_id="req-123",
            path="/api/v1/test",
            errors=[],
        )
        assert response.error == "ValidationError"
        assert response.message == "Validation failed"
        assert response.code == "VALIDATION_ERROR"
        assert response.details == {"count": 2}
        assert response.request_id == "req-123"
        assert response.path == "/api/v1/test"

    def test_json_serialization_with_errors(self):
        """Test JSON serialization includes errors."""
        errors = [
            ErrorDetail(field="email", message="Invalid", code="invalid"),
        ]
        response = ValidationErrorResponse(
            error="ValidationError",
            message="Validation failed",
            code="VALIDATION_ERROR",
            errors=errors,
        )
        json_data = response.model_dump(mode="json")
        assert "errors" in json_data
        assert len(json_data["errors"]) == 1
        assert json_data["errors"][0]["field"] == "email"


class TestErrorResponseExamples:
    """Test error response schema examples for common scenarios."""

    def test_404_not_found_response(self):
        """Test creating a 404 Not Found response."""
        response = ErrorResponse(
            error="ResourceNotFoundError",
            message="User not found",
            code="USER_NOT_FOUND",
            details={"user_id": 123},
            request_id="req-abc-123",
            path="/api/v1/users/123",
        )
        json_data = response.model_dump(mode="json")
        assert json_data["error"] == "ResourceNotFoundError"
        assert json_data["code"] == "USER_NOT_FOUND"

    def test_401_unauthorized_response(self):
        """Test creating a 401 Unauthorized response."""
        response = ErrorResponse(
            error="InvalidCredentialsError",
            message="Invalid username or password",
            code="INVALID_CREDENTIALS",
            request_id="req-xyz-789",
            path="/api/v1/auth/login",
        )
        json_data = response.model_dump(mode="json")
        assert json_data["error"] == "InvalidCredentialsError"
        assert json_data["code"] == "INVALID_CREDENTIALS"

    def test_422_validation_response(self):
        """Test creating a 422 Validation response."""
        response = ValidationErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            code="VALIDATION_ERROR",
            details={"error_count": 2},
            errors=[
                ErrorDetail(
                    field="body.email",
                    message="value is not a valid email address",
                    code="value_error.email",
                ),
                ErrorDetail(
                    field="body.password",
                    message="String should have at least 8 characters",
                    code="string_too_short",
                ),
            ],
            request_id="req-val-456",
            path="/api/v1/auth/register",
        )
        json_data = response.model_dump(mode="json")
        assert json_data["error"] == "ValidationError"
        assert len(json_data["errors"]) == 2
        assert json_data["details"]["error_count"] == 2
