"""Current user model for request context."""

from dataclasses import dataclass
from typing import Any

from starlette.requests import Request


@dataclass
class CurrentUser:
    """Current authenticated user context."""

    user_id: int
    username: str
    email: str
    role: str

    @classmethod
    def from_request(cls, request: Request) -> "CurrentUser | None":
        """Extract current user from request state."""
        if hasattr(request.state, "user"):
            user_data: dict[str, Any] = request.state.user
            return cls(
                user_id=user_data.get("user_id", 0),
                username=user_data.get("username", ""),
                email=user_data.get("email", ""),
                role=user_data.get("role", ""),
            )
        return None

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == "admin"

    def is_privileged(self) -> bool:
        """Check if user has privileged access (admin or manager)."""
        return self.role in {"admin", "project_manager"}
