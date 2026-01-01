"""API路由配置"""

from fastapi import APIRouter

from api.rest import auth, checkpoint, training

# 创建API路由器
api_router = APIRouter()

# 注册认证路由
api_router.include_router(auth.router)

# 注册训练任务路由
api_router.include_router(training.router)

# 注册Checkpoint路由
api_router.include_router(checkpoint.router)

# 健康检查端点
@api_router.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "AI Training Platform API"}


@api_router.get("/", tags=["根路径"])
async def root():
    """API根路径"""
    return {
        "name": "AI Training Platform API",
        "version": "1.0.0",
        "description": "基于AWS SageMaker HyperPod的企业级AI训练平台",
    }


__all__ = ["api_router"]
