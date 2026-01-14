"""API V1 - Version 1 REST endpoints.

Contains:
- Endpoints: REST route handlers
- Schemas: Pydantic request/response models
- Dependencies: FastAPI dependency injection
"""

from fastapi import APIRouter

from src.api.v1.endpoints.auth import router as auth_router

router = APIRouter(prefix="/v1")

# Register endpoint routers
router.include_router(auth_router)
