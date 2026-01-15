"""Path configuration for middleware - Single source of truth for exempt paths."""

# Paths exempt from authentication (health checks, docs, public auth endpoints)
AUTH_EXEMPT_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/healthz",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/token/refresh",
        "/api/v1/auth/password-reset/request",
        "/api/v1/auth/password-reset/confirm",
    }
)

# Regex patterns for auth exempt paths
AUTH_EXEMPT_PATTERNS: tuple[str, ...] = (r"^/api/v1/auth/password-reset/.*$",)

# Paths exempt from audit logging (subset of auth exempt - only internal endpoints)
AUDIT_EXEMPT_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/healthz",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)

# Path prefixes exempt from audit logging
AUDIT_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/docs/",
    "/redoc/",
)
