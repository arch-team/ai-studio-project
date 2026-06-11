"""AI Training Platform - FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.modules.audit.api.middleware import AuditMiddleware
from src.router import api_router
from src.shared.api import (
    domain_exception_handler,
    problem_exception_handler,
    security_exception_handler,
)
from src.shared.api.middleware import (
    AuthenticationMiddleware,
    ErrorHandlerMiddleware,
    PerformanceMiddleware,
    TracingMiddleware,
)
from src.shared.domain.exceptions import DomainError
from src.shared.domain.problem import Problem
from src.shared.infrastructure import configure_logging, get_settings
from src.shared.infrastructure.config import Settings
from src.shared.infrastructure.database import AsyncSessionLocal, import_all_models
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

    # 启动审计日志自动清理后台任务（每日凌晨 2:00 北京时间执行）
    from src.modules.audit.application import AuditCleanupService
    from src.modules.audit.infrastructure import AuditLogRepositoryImpl

    # 后台任务模式：通过工厂在每次清理时创建新的 session + repository
    cleanup_service = AuditCleanupService(
        session_factory=AsyncSessionLocal,
        repository_factory=lambda session: AuditLogRepositoryImpl(session),
    )
    await cleanup_service.start_scheduled_cleanup()

    logger.info(
        "application_started",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    yield

    # 停止审计日志清理后台任务
    await cleanup_service.stop_scheduled_cleanup()
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

    # OpenAPI 标签元数据，用于 Swagger UI / ReDoc 分组展示
    openapi_tags = [
        {"name": "Health", "description": "健康检查端点"},
        {"name": "认证", "description": "用户登录、注册、Token 管理"},
        {"name": "用户管理", "description": "用户 CRUD、角色分配"},
        {"name": "训练任务", "description": "训练任务提交、状态查询、停止"},
        {"name": "任务模板", "description": "训练任务模板管理"},
        {"name": "模型", "description": "模型注册、版本管理"},
        {"name": "资源限制配置", "description": "全局资源限制策略配置"},
        {"name": "资源配额", "description": "团队/用户资源配额管理"},
        {"name": "数据集", "description": "数据集版本管理、文件上传"},
        {"name": "开发空间", "description": "开发空间生命周期管理"},
        {"name": "审计日志", "description": "操作审计日志查询"},
        {"name": "监控", "description": "训练任务监控、指标查询"},
        {"name": "计费报表", "description": "成本统计与计费报表"},
    ]

    return FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Enterprise AI Training Platform powered by AWS SageMaker HyperPod。\n\n"
            "提供分布式训练管理、资源调度、数据集管理、检查点管理和多租户支持等核心能力。"
        ),
        docs_url="/docs" if is_dev else None,
        redoc_url="/redoc" if is_dev else None,
        openapi_url="/openapi.json" if is_dev else None,
        openapi_tags=openapi_tags,
        lifespan=lifespan,
    )


def _configure_middleware(app: FastAPI, settings: Settings) -> None:
    """配置中间件层。

    执行顺序 (LIFO - Last In, First Out):
    Request:  ErrorHandler → Performance → Tracing → CORS → Auth → Audit
    Response: Audit → Auth → CORS → Tracing → Performance → ErrorHandler
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
    app.add_middleware(PerformanceMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)


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

    # 全局异常处理器（兜底，中间件层已处理大部分异常）
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """兜底异常处理器：捕获中间件层未拦截的异常。"""
        trace_id = getattr(request.state, "trace_id", None)
        logger.error(
            "unhandled_exception_fallback",
            exc_info=exc,
            trace_id=trace_id,
            path=request.url.path,
            method=request.method,
        )
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
        """Liveness check - 应用进程存活。"""
        base: dict = {"status": "healthy"}
        if settings.environment == "development":
            base.update({"version": settings.app_version, "environment": settings.environment})
        return base

    @app.get("/health/ready", tags=["Health"], response_model=None)
    async def _readiness_check() -> JSONResponse | dict:
        """Readiness check - 验证数据库连接等关键依赖可用。"""
        checks: dict = {}
        is_ready = True

        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {type(e).__name__}"
            is_ready = False

        if not is_ready:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "checks": checks},
            )
        return {"status": "ready", "checks": checks}


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
