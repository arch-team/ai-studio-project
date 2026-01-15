"""Quota status value object."""

from enum import Enum


class QuotaStatus(Enum):
    """Quota status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
