"""API V1 Dependencies - FastAPI dependency injection.

Dependencies for endpoint injection:
- get_db: Database session dependency
- get_current_user: Authentication dependency
- get_service: Application service dependencies
- permissions: Resource ownership and access control utilities
"""

from src.api.v1.dependencies.permissions import (
    check_resource_owner_or_privileged,
    get_owner_filter,
    is_privileged_user,
)
from src.api.v1.dependencies.services import (
    get_account_service,
    get_auth_service,
    get_password_service,
)

__all__ = [
    "get_account_service",
    "get_auth_service",
    "get_password_service",
    "check_resource_owner_or_privileged",
    "get_owner_filter",
    "is_privileged_user",
]
