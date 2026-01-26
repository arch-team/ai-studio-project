"""LoginAttempt domain entity - Records login attempts for audit and security."""

from datetime import datetime

from pydantic import Field

from src.shared.domain import PydanticEntity
from src.shared.utils import utc_now


class LoginAttempt(PydanticEntity):
    """Login attempt domain entity for tracking authentication events."""

    username: str = Field(min_length=1)
    ip_address: str
    success: bool
    user_id: int | None = None
    user_agent: str | None = None
    failure_reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

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
