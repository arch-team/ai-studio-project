"""AI Training Platform - FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.modules.audit.api.middleware import AuditMiddleware
from src.router import api_router
from src.shared.api import (
    domain_exception_handler,
    problem_exception_handler,
    security_exception_handler,
)
from src.shared.api.middleware import AuthenticationMiddleware, TracingMiddleware
from src.shared.domain.exceptions import DomainError
from src.shared.domain.problem import Problem
from src.shared.infrastructure import configure_logging, get_settings
from src.shared.infrastructure.database import AsyncSessionLocal
from src.shared.infrastructure.config import Settings
from src.shared.infrastructure.database import import_all_models
from src.shared.infrastructure.security.exceptions import SecurityError

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle manager."""
    # 初始化结构化日志
    settings = get_settings()
    configure_logging(level=settings.log_level)

    # 确保所有 ORM 模型在启动时被加载，解决 relationship 字符串引用问题
    import_all_models()

    # 注入审计日志 session factory 到 app.state（中间件不在 DI 体系内）
    app.state.audit_session_factory = AsyncSessionLocal

    logger.info(
        "application_started",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    yield

    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = _create_base_app(settings)
    _configure_middleware(app, settings)
    _configure_routing(app)
    _configure_exception_handlers(app)
    _configure_health_check(app, settings)

    return app


def _create_base_app(settings: Settings) -> FastAPI:
    """创建基础 FastAPI 应用实例。非 development 环境禁用 API 文档端点。"""
    is_dev = settings.environment == "development"
    return FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise AI Training Platform powered by AWS SageMaker HyperPod",
        docs_url="/docs" if is_dev else None,
        redoc_url="/redoc" if is_dev else None,
        openapi_url="/openapi.json" if is_dev else None,
        lifespan=lifespan,
    )


def _configure_middleware(app: FastAPI, settings: Settings) -> None:
    """配置中间件层。

    执行顺序 (LIFO - Last In, First Out):
    Request:  Tracing → CORS → Auth → Audit
    Response: Audit → Auth → CORS → Tracing
    """
    # 按逆序添加以实现期望的执行顺序
    app.add_middleware(AuditMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Accept-Language", "Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(TracingMiddleware)


def _configure_routing(app: FastAPI) -> None:
    """配置 API 路由。"""
    app.include_router(api_router)


def _configure_exception_handlers(app: FastAPI) -> None:
    """配置异常处理器。"""
    # Problem 处理器用于新的 dataclass 异常体系
    app.add_exception_handler(Problem, problem_exception_handler)  # type: ignore[arg-type]
    # 旧的处理器用于向后兼容（迁移完成后移除）
    app.add_exception_handler(DomainError, domain_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(SecurityError, security_exception_handler)  # type: ignore[arg-type]

    # 全局异常处理器
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unhandled exceptions and return 500 response."""
        trace_id = getattr(request.state, "trace_id", None)
        error_response: dict = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
            }
        }
        if trace_id:
            error_response["error"]["trace_id"] = trace_id
        return JSONResponse(status_code=500, content=error_response)


def _configure_health_check(app: FastAPI, settings: Settings) -> None:
    """配置健康检查端点。非 development 环境仅返回 status，避免版本信息泄露。"""

    @app.get("/health", tags=["Health"])
    async def _health_check() -> dict:
        """Health check endpoint for load balancers and monitoring."""
        base: dict = {"status": "healthy"}
        if settings.environment == "development":
            base.update({"version": settings.app_version, "environment": settings.environment})
        return base


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
