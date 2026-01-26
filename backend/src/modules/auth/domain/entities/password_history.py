"""PasswordHistory domain entity - Tracks password changes for security compliance."""

from datetime import datetime

from pydantic import Field

from src.shared.domain import PydanticEntity
from src.shared.utils import utc_now


class PasswordHistory(PydanticEntity):
    """Password history domain entity for tracking password changes."""

    user_id: int
    password_hash: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def create(cls, user_id: int, password_hash: str) -> "PasswordHistory":
        """Create a new password history entry."""
        return cls(
            id=None,
            user_id=user_id,
            password_hash=password_hash,
        )
