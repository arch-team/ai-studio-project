"""API Router - Aggregates all module routers.

This module collects routers from all feature modules and
registers them with the FastAPI application.
"""

from fastapi import APIRouter

# Import module routers
# TODO: Uncomment as modules are migrated
from src.modules.auth.api.endpoints import router as auth_router
from src.modules.training.api.endpoints import router as training_router
from src.modules.models.api.endpoints import router as models_router
from src.modules.quotas.api.endpoints import router as quotas_router
from src.modules.datasets.api.endpoints import router as datasets_router
from src.modules.spaces.api.endpoints import router as spaces_router
from src.modules.audit.api.endpoints import router as audit_router

# API v1 router
api_router = APIRouter(prefix="/api/v1")

# Register module routers
# TODO: Uncomment as modules are migrated
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(training_router, prefix="/training-jobs", tags=["训练任务"])
api_router.include_router(models_router, prefix="/models", tags=["模型"])
api_router.include_router(quotas_router, prefix="/resource-limit-configs", tags=["资源限制配置"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["数据集"])
api_router.include_router(spaces_router, prefix="/spaces", tags=["开发空间"])
api_router.include_router(audit_router, prefix="/audit-logs", tags=["审计日志"])

__all__ = ["api_router"]
