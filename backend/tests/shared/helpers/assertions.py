"""Custom assertions for domain testing."""

from typing import Any

from src.shared.domain.exceptions import (
    DomainError,
    EntityNotFoundError,
    ValidationError,
)


def assert_entity_equal(
    actual: Any,
    expected: Any,
    exclude_fields: list[str] | None = None,
) -> None:
    """Assert two entities are equal, optionally excluding certain fields.

    Args:
        actual: The actual entity
        expected: The expected entity
        exclude_fields: Fields to exclude from comparison (e.g., ['created_at', 'updated_at'])
    """
    exclude = set(exclude_fields or [])

    actual_dict = actual.__dict__ if hasattr(actual, "__dict__") else actual
    expected_dict = expected.__dict__ if hasattr(expected, "__dict__") else expected

    for key, value in expected_dict.items():
        if key.startswith("_") or key in exclude:
            continue
        assert key in actual_dict, f"Missing field: {key}"
        assert actual_dict[key] == value, f"Field {key}: {actual_dict[key]} != {value}"


def assert_validation_error(
    error: Exception,
    expected_message: str | None = None,
) -> None:
    """Assert that an exception is a ValidationError with optional message check.

    Args:
        error: The exception to check
        expected_message: Optional substring to check in the error message
    """
    assert isinstance(error, ValidationError), f"Expected ValidationError, got {type(error)}"
    if expected_message:
        assert expected_message in str(error), f"'{expected_message}' not in '{error}'"


def assert_not_found_error(
    error: Exception,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> None:
    """Assert that an exception is an EntityNotFoundError.

    Args:
        error: The exception to check
        entity_type: Optional entity type to verify
        entity_id: Optional entity ID to verify
    """
    assert isinstance(error, EntityNotFoundError), f"Expected EntityNotFoundError, got {type(error)}"
    if entity_type:
        assert error.entity_type == entity_type, f"Entity type: {error.entity_type} != {entity_type}"
    if entity_id:
        assert error.entity_id == entity_id, f"Entity ID: {error.entity_id} != {entity_id}"


def assert_domain_error(
    error: Exception,
    error_type: type[DomainError] | None = None,
    message_contains: str | None = None,
) -> None:
    """Assert that an exception is a DomainError of specific type.

    Args:
        error: The exception to check
        error_type: Optional specific DomainError subclass
        message_contains: Optional substring to check in the error message
    """
    assert isinstance(error, DomainError), f"Expected DomainError, got {type(error)}"
    if error_type:
        assert isinstance(error, error_type), f"Expected {error_type.__name__}, got {type(error).__name__}"
    if message_contains:
        assert message_contains in str(error), f"'{message_contains}' not in '{error}'"
