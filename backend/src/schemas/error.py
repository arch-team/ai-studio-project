"""Standardized error response schemas.

Provides consistent error response format for all API errors,
enabling better client-side error handling and debugging.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information for field-level validation errors."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response format for all API errors.

    This provides a consistent error structure across all endpoints,
    enabling better client-side error handling and debugging.
    """

    error: str = Field(..., description="Error type identifier (exception class name)")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(
        ..., description="Application error code for programmatic handling"
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error context and debugging information",
    )
    request_id: Optional[str] = Field(
        None, description="Request ID for tracing and support"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error occurrence timestamp (UTC)",
    )
    path: Optional[str] = Field(
        None, description="Request path that caused the error"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ResourceNotFoundError",
                "message": "Account not found",
                "code": "ACCOUNT_NOT_FOUND",
                "details": {"username": "john_doe"},
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "path": "/api/v1/auth/local-accounts/john_doe",
            }
        }
    }


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-level details.

    Used for Pydantic validation errors (HTTP 422).
    """

    errors: list[ErrorDetail] = Field(
        default_factory=list, description="List of validation errors by field"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "message": "Request validation failed",
                "code": "VALIDATION_ERROR",
                "details": {"error_count": 2},
                "errors": [
                    {
                        "field": "body.email",
                        "message": "value is not a valid email address",
                        "code": "value_error.email",
                    },
                    {
                        "field": "body.password",
                        "message": "String should have at least 8 characters",
                        "code": "string_too_short",
                    },
                ],
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "path": "/api/v1/auth/local-accounts",
            }
        }
    }
