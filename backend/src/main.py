"""FastAPI应用程序入口

提供应用工厂函数和开发服务器启动
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.exception_handler import register_exception_handlers
from api.middleware.logging import RequestLoggingMiddleware
from api.router import api_router
from config.database import close_db, init_db
from config.logging import setup_logging
from config.settings import settings

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理

    启动时初始化数据库连接池
    关闭时清理资源
    """
    logger.info("应用启动: 初始化数据库连接...")
    await init_db()
    logger.info("数据库连接初始化完成")

    yield

    logger.info("应用关闭: 清理资源...")
    await close_db()
    logger.info("资源清理完成")


def create_app() -> FastAPI:
    """创建FastAPI应用实例

    Returns:
        FastAPI: 配置好的FastAPI应用实例
    """
    app = FastAPI(
        title="AI Training Platform API",
        description="基于AWS SageMaker HyperPod的企业级AI训练平台",
        version="1.0.0",
        docs_url="/api/docs" if settings.environment == "development" else None,
        redoc_url="/api/redoc" if settings.environment == "development" else None,
        openapi_url="/api/openapi.json" if settings.environment == "development" else None,
        lifespan=lifespan,
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)

    # 注册异常处理器
    register_exception_handlers(app)

    # 注册API路由
    app.include_router(api_router, prefix="/api/v1")

    logger.info(f"FastAPI应用创建成功 (环境: {settings.environment})")

    return app


# 创建应用实例
app = create_app()


def main():
    """启动开发服务器"""
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_config=None,  # 使用自定义日志配置
    )


if __name__ == "__main__":
    main()
