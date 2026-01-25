"""AI Training Platform - FastAPI Application Entry Point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.modules.audit.api.middleware import AuditMiddleware
from src.router import api_router
from src.shared.api import (
    domain_exception_handler,
    security_exception_handler,
)
from src.shared.api.middleware import AuthenticationMiddleware, TracingMiddleware
from src.shared.domain.exceptions import DomainError
from src.shared.infrastructure import get_settings
from src.shared.infrastructure.security.exceptions import SecurityError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle manager."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    yield

    logger.info("Shutting down application...")


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
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(SecurityError, security_exception_handler)

    # Global exception handler for unhandled exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
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
