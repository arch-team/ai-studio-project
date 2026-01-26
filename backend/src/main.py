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

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise AI Training Platform powered by AWS SageMaker HyperPod",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware execution order (LIFO - Last In, First Out):
    # Request:  Tracing → CORS → Auth → Audit
    # Response: Audit → Auth → CORS → Tracing
    #
    # To achieve this, add in reverse order:
    # 1. Audit   (added first, executes last on request)
    # 2. Auth    (added second)
    # 3. CORS    (added third)
    # 4. Tracing (added last, executes first on request - provides trace_id)

    app.add_middleware(AuditMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Authorization",
            "Content-Type",
            "X-Request-ID",
        ],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(TracingMiddleware)

    # Register API routers
    app.include_router(api_router)

    # Register exception handlers (more specific first)
    # Problem 处理器用于新的 dataclass 异常体系
    # Starlette 类型签名过于严格，运行时类型匹配是正确的
    app.add_exception_handler(Problem, problem_exception_handler)  # type: ignore[arg-type]
    # 旧的处理器用于向后兼容（迁移完成后移除）
    app.add_exception_handler(DomainError, domain_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(SecurityError, security_exception_handler)  # type: ignore[arg-type]

    # Global exception handler for unhandled exceptions
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

    @app.get("/health", tags=["Health"])
    async def _health_check() -> dict:
        """Health check endpoint for load balancers and monitoring."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        }

    return app


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
