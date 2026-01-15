"""Common API Schemas - Shared request/response models.

This module contains schemas that are shared across multiple endpoints,
including standard error responses and pagination.
"""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response schema.

    All API error responses should use this schema for consistency.
    """

    code: str = Field(..., description="Error code (e.g., UNAUTHORIZED, NOT_FOUND)")
    message: str = Field(..., description="Human-readable error message")
    details: dict | None = Field(None, description="Additional error details")

    model_config = {"json_schema_extra": {"example": {"code": "NOT_FOUND", "message": "Resource not found", "details": None}}}


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel):
    """Base class for paginated responses."""

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
