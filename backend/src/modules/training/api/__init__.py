"""Training API layer - REST endpoints, schemas, and dependencies."""

from .endpoints import router
from .endpoints import router as training_jobs_router
from .job_templates import router as job_templates_router

__all__ = [
    "router",  # 保持向后兼容
    "training_jobs_router",
    "job_templates_router",
]
