"""Training API endpoints - 聚合子路由。"""

from fastapi import APIRouter

from .checkpoints import router as checkpoints_router
from .metrics import router as metrics_router
from .training_jobs import router as training_jobs_router

router = APIRouter()

# 注意顺序：先注册 compare-metrics 等无 {job_id} 的路由
# 直接扩展 routes 列表以避免 FastAPI 对空前缀+空路径的限制
router.routes.extend(metrics_router.routes)
router.routes.extend(training_jobs_router.routes)
router.routes.extend(checkpoints_router.routes)
