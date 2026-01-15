"""AI Training Platform - FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.shared.api import (
    domain_exception_handler,
    security_exception_handler,
)
from src.modules.audit.api.middleware import AuditMiddleware
from src.shared.infrastructure.security.exceptions import SecurityError
from src.shared.domain.exceptions import DomainError
from src.shared.api.middleware import AuthenticationMiddleware
from src.router import api_router
from src.shared.infrastructure import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle manager."""
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")

    yield

    print("Shutting down application...")


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
    # Request:  CORS → Auth → Audit
    # Response: Audit → Auth → CORS
    #
    # To achieve this, add in reverse order:
    # 1. Audit (added first, executes last on request)
    # 2. Auth  (added second)
    # 3. CORS  (added last, executes first on request)

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
    )

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
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error_type": type(exc).__name__,
            },
        )

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
