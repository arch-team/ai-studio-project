"""Datetime utilities with timezone awareness."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)
