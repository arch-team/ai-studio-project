"""API V1 Dependencies - FastAPI dependency injection.

Dependencies for endpoint injection:
- get_db: Database session dependency
- get_current_user: Authentication dependency
- get_service: Application service dependencies
"""

from src.api.v1.dependencies.services import get_auth_service

__all__ = ["get_auth_service"]
