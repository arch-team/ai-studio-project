"""API V1 - Version 1 REST endpoints.

Contains:
- Endpoints: REST route handlers
- Schemas: Pydantic request/response models
- Dependencies: FastAPI dependency injection
"""

from fastapi import APIRouter

router = APIRouter(prefix="/v1")
