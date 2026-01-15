"""Authentication type value object."""

from enum import Enum


class AuthType(Enum):
    """Authentication type enumeration."""

    SSO = "sso"
    LOCAL = "local"
