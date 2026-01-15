"""PasswordHistory domain entity - Tracks password changes for security compliance."""

from dataclasses import dataclass, field
from datetime import datetime

from src.shared.utils import utc_now


@dataclass
class PasswordHistory:
    """Password history domain entity for tracking password changes."""

    id: int | None
    user_id: int
    password_hash: str
    created_at: datetime = field(default_factory=utc_now)

    @classmethod
    def create(cls, user_id: int, password_hash: str) -> "PasswordHistory":
        """Create a new password history entry."""
        return cls(
            id=None,
            user_id=user_id,
            password_hash=password_hash,
        )
