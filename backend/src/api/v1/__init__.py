"""API V1 - Version 1 REST endpoints.

Contains:
- Endpoints: REST route handlers
- Schemas: Pydantic request/response models
- Dependencies: FastAPI dependency injection
"""

from fastapi import APIRouter

from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.models import router as models_router
from src.api.v1.endpoints.resource_limit_configs import (
    router as resource_limit_configs_router,
)
from src.api.v1.endpoints.training_jobs import router as training_jobs_router

router = APIRouter(prefix="/v1")

# Register endpoint routers
router.include_router(auth_router)
router.include_router(training_jobs_router)
router.include_router(models_router)
router.include_router(resource_limit_configs_router)
