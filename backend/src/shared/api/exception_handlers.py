"""Global Exception Handlers - Centralized exception to HTTP response mapping."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.shared.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    ResourceQuotaExceededError,
    ValidationError,
)
from src.shared.infrastructure.security.exceptions import (
    AccountLockedError,
    AccountValidationError,
    AuthenticationError,
    InsufficientPermissionsError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordExpiredError,
    PasswordHistoryViolationError,
    PasswordTooWeakError,
    SecurityError,
    SSODegradedModeError,
    SSOError,
    TokenExpiredError,
    UserNotFoundError,
)

# Domain exception → HTTP status code mapping
DOMAIN_EXCEPTION_MAP: dict[type[DomainError], int] = {
    EntityNotFoundError: status.HTTP_404_NOT_FOUND,
    DuplicateEntityError: status.HTTP_409_CONFLICT,
    InvalidStateTransitionError: status.HTTP_409_CONFLICT,
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    ResourceQuotaExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
}

# Security exception → HTTP status code mapping
SECURITY_EXCEPTION_MAP: dict[type[SecurityError], int] = {
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    AccountValidationError: status.HTTP_400_BAD_REQUEST,
    TokenExpiredError: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    AccountLockedError: status.HTTP_423_LOCKED,
    PasswordExpiredError: status.HTTP_401_UNAUTHORIZED,
    PasswordTooWeakError: status.HTTP_400_BAD_REQUEST,
    PasswordHistoryViolationError: status.HTTP_400_BAD_REQUEST,
    InsufficientPermissionsError: status.HTTP_403_FORBIDDEN,
    SSOError: status.HTTP_401_UNAUTHORIZED,
    SSODegradedModeError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Handle all Domain layer exceptions."""
    # First try exact type match
    status_code = DOMAIN_EXCEPTION_MAP.get(type(exc))

    # If no exact match, check inheritance chain
    if status_code is None:
        for exc_type, code in DOMAIN_EXCEPTION_MAP.items():
            if isinstance(exc, exc_type):
                status_code = code
                break

    # Default to 400 if no match found
    if status_code is None:
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": exc.message,
            "error_type": type(exc).__name__,
        },
    )


async def security_exception_handler(
    request: Request, exc: SecurityError
) -> JSONResponse:
    """Handle all Security layer exceptions."""
    status_code = SECURITY_EXCEPTION_MAP.get(type(exc), status.HTTP_401_UNAUTHORIZED)

    content: dict = {
        "detail": exc.message,
        "error_code": exc.code,
    }

    # Include additional context for specific exceptions
    if isinstance(exc, AccountLockedError) and exc.locked_until:
        content["locked_until"] = exc.locked_until
    elif isinstance(exc, PasswordTooWeakError):
        content["violations"] = exc.violations

    return JSONResponse(status_code=status_code, content=content)
