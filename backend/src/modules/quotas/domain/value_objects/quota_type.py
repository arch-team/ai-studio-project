"""Quota type value object."""

from enum import Enum


class QuotaType(Enum):
    """Quota allocation type."""

    USER = "user"
    TEAM = "team"
    PROJECT = "project"
