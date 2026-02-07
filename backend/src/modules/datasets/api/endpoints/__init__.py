"""数据集 API 端点模块。

将大型 endpoints.py 拆分为多个专门的路由文件:
- datasets.py: 数据集 CRUD 操作
- upload.py: 分片上传相关端点
- fsx.py: FSx 同步相关端点
"""

from fastapi import APIRouter

from .datasets import router as datasets_router
from .fsx import router as fsx_router
from .upload import router as upload_router

# 创建主路由器并包含所有子路由
router = APIRouter()

# 将所有路由合并到主路由器
# 注意：datasets_router 和 fsx_router 的路由路径已经在各自文件中定义
for route in datasets_router.routes:
    router.routes.append(route)

for route in fsx_router.routes:
    router.routes.append(route)

# upload 路由需要特定前缀
router.include_router(upload_router, prefix="/{dataset_id}/upload", tags=["upload"])

__all__ = ["router"]
