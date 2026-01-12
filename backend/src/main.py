"""FastAPI application entry point.

Task: T016 - 配置 FastAPI 应用入口
注册路由,配置 CORS,集成认证中间件,配置 OpenAPI docs
(TLS 终止由 T008i ALB 处理,应用无需配置 HTTPS)
"""

from contextlib import asynccontextmanager
from datetime import datetime

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.config import get_settings
from src.core.exceptions import AppException, get_http_status_code
from src.schemas.error import ErrorDetail, ErrorResponse, ValidationErrorResponse
from src.api.v1.router import api_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events handler."""
    # Startup
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Initialize database connection pool (placeholder for async session)
    # from src.core.database import init_db
    # await init_db()

    yield

    # Shutdown
    logger.info("application_shutdown")
    # Close database connections
    # from src.core.database import close_db
    # await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Training Platform API - 基于 AWS SageMaker HyperPod 的企业级 AI 训练平台",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
)


# === Exception Handlers ===


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Automatic handler for all AppException subclasses.

    Maps AppException to appropriate HTTP status code and returns
    standardized error response.
    """
    status_code = get_http_status_code(exc)
    request_id = getattr(request.state, "request_id", None)

    # Structured logging with appropriate level
    log_method = logger.error if status_code >= 500 else logger.warning
    log_method(
        "app_exception",
        error_type=type(exc).__name__,
        error_code=exc.code,
        message=exc.message,
        details=exc.details,
        path=str(request.url.path),
        method=request.method,
        status_code=status_code,
        request_id=request_id,
        exc_info=status_code >= 500,
    )

    error_response = ErrorResponse(
        error=type(exc).__name__,
        message=exc.message,
        code=exc.code,
        details=exc.details,
        request_id=request_id,
        path=str(request.url.path),
    )

    headers = {}
    if status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(mode="json"),
        headers=headers or None,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with detailed field information."""
    request_id = getattr(request.state, "request_id", None)

    error_details = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        error_details.append(
            ErrorDetail(
                field=field_path,
                message=error["msg"],
                code=error["type"],
            )
        )

    logger.warning(
        "validation_error",
        path=str(request.url.path),
        method=request.method,
        errors=[e.model_dump() for e in error_details],
        request_id=request_id,
    )

    error_response = ValidationErrorResponse(
        error="ValidationError",
        message="Request validation failed",
        code="VALIDATION_ERROR",
        details={"error_count": len(error_details)},
        errors=error_details,
        request_id=request_id,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(mode="json"),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTPException with standardized format."""
    request_id = getattr(request.state, "request_id", None)

    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url.path),
        method=request.method,
        request_id=request_id,
    )

    error_response = ErrorResponse(
        error="HTTPException",
        message=str(exc.detail) if exc.detail else "HTTP error",
        code=f"HTTP_{exc.status_code}",
        request_id=request_id,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global handler for unhandled exceptions."""
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error=str(exc),
        path=str(request.url.path),
        method=request.method,
        request_id=request_id,
        exc_info=True,
    )

    error_response = ErrorResponse(
        error="InternalServerError",
        message="An unexpected error occurred",
        code="INTERNAL_ERROR",
        request_id=request_id,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to each request for tracing."""
    import uuid

    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Add to structlog context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = datetime.utcnow()

    response = await call_next(request)

    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
        client_ip=request.client.host if request.client else None,
    )

    return response


# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer and Kubernetes probes."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes.

    This endpoint should verify all dependencies are ready.
    """
    # TODO: Add database connectivity check
    # TODO: Add external service connectivity checks

    return {
        "status": "ready",
        "checks": {
            "database": "ok",  # Placeholder
            "cache": "ok",  # Placeholder
        },
    }
