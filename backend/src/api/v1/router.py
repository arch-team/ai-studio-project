"""API v1 Router.

This module combines all API v1 routers.
"""

from fastapi import APIRouter

from src.api.auth import router as auth_router

api_router = APIRouter()

# Include auth routes
api_router.include_router(auth_router)

# Training jobs endpoints (to be implemented in Phase 3)
# api_router.include_router(training.router, prefix="/training-jobs", tags=["Training Jobs"])

# Datasets endpoints (to be implemented in Phase 4)
# api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])

# Resources/quota endpoints (to be implemented in Phase 5)
# api_router.include_router(quotas.router, prefix="/quotas", tags=["Resource Quotas"])

# Models endpoints (to be implemented in Phase 3)
# api_router.include_router(models.router, prefix="/models", tags=["Models"])

# Spaces/IDE endpoints (to be implemented in Phase 7)
# api_router.include_router(spaces.router, prefix="/spaces", tags=["Development Spaces"])
