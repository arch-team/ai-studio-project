"""Datetime utilities with timezone awareness."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(UTC)
