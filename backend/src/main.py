"""AI Training Platform - FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.audit import AuditMiddleware
from src.api.middleware.auth import AuthenticationMiddleware
from src.api.v1 import router as v1_router
from src.infrastructure.config import get_settings


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

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add authentication middleware
    app.add_middleware(AuthenticationMiddleware)

    # Add audit logging middleware (after auth to access user_id)
    app.add_middleware(AuditMiddleware)

    # Register API routers
    app.include_router(v1_router, prefix="/api")

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
