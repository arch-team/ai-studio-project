"""Permission Dependencies - Resource ownership and access control utilities."""

from fastapi import HTTPException, status

from src.api.middleware.auth import CurrentUser

# Roles that can access any user's resources
PRIVILEGED_ROLES = frozenset({"admin", "manager"})


def check_resource_owner_or_privileged(
    resource_owner_id: int,
    current_user: CurrentUser,
    resource_type: str = "resource",
    action: str = "access",
) -> None:
    """Check if user owns the resource or has privileged access.

    Args:
        resource_owner_id: The owner ID of the resource
        current_user: The authenticated user
        resource_type: Human-readable resource name for error messages
        action: Action being performed (e.g., "view", "edit", "delete")

    Raises:
        HTTPException: 403 if user lacks permission
    """
    if is_privileged_user(current_user):
        return

    if resource_owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to {action} this {resource_type}",
        )


def is_privileged_user(current_user: CurrentUser) -> bool:
    """Check if user has privileged (admin/manager) access."""
    return current_user.role in PRIVILEGED_ROLES


def get_owner_filter(current_user: CurrentUser) -> int | None:
    """Get owner_id filter for list queries.

    Returns None for privileged users (no filter), or user_id for regular users.
    """
    if is_privileged_user(current_user):
        return None
    return current_user.user_id
