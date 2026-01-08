"""API v1 router configuration."""

from fastapi import APIRouter

api_router = APIRouter()

# Training jobs endpoints (to be implemented in Phase 3)
# api_router.include_router(training.router, prefix="/training", tags=["training"])

# Datasets endpoints (to be implemented in Phase 4)
# api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])

# Resources/quota endpoints (to be implemented in Phase 5)
# api_router.include_router(resources.router, prefix="/resources", tags=["resources"])

# Spaces/IDE endpoints (to be implemented in Phase 7)
# api_router.include_router(spaces.router, prefix="/spaces", tags=["spaces"])
