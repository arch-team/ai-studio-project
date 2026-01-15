"""LoginAttempt domain entity - Records login attempts for audit and security."""

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.utils import utc_now


@dataclass
class LoginAttempt:
    """Login attempt domain entity for tracking authentication events."""

    id: int | None
    username: str
    ip_address: str
    success: bool
    user_id: int | None = None
    user_agent: str | None = None
    failure_reason: str | None = None
    created_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create_failed(
        cls,
        username: str,
        ip_address: str,
        failure_reason: str,
        user_id: int | None = None,
        user_agent: str | None = None,
    ) -> "LoginAttempt":
        """Create a failed login attempt record."""
        return cls(
            id=None,
            username=username,
            ip_address=ip_address,
            success=False,
            user_id=user_id,
            user_agent=user_agent,
            failure_reason=failure_reason,
        )

    @classmethod
    def create_successful(
        cls,
        username: str,
        ip_address: str,
        user_id: int,
        user_agent: str | None = None,
    ) -> "LoginAttempt":
        """Create a successful login attempt record."""
        return cls(
            id=None,
            username=username,
            ip_address=ip_address,
            success=True,
            user_id=user_id,
            user_agent=user_agent,
            failure_reason=None,
        )
