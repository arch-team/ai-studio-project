"""AI Training Platform - FastAPI Application Entry Point.

This is the main entry point for the FastAPI application.
It configures middleware, routes, and application lifecycle events.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.auth import AuthenticationMiddleware
from src.api.v1 import router as v1_router
from src.infrastructure.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")

    yield

    # Shutdown
    print("Shutting down application...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
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

    # Register API routers
    app.include_router(v1_router, prefix="/api")

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
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
