"""Auth domain exceptions."""

from src.shared.domain import DomainError


class AuthError(DomainError):
    """Base exception for authentication errors."""


class UserNotFoundError(AuthError):
    """Raised when user is not found."""

    def __init__(self, identifier: str | int):
        self.identifier = identifier
        super().__init__(f"User not found: {identifier}")


class InvalidCredentialsError(AuthError):
    """Raised when credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message)


class AccountLockedError(AuthError):
    """Raised when account is locked."""

    def __init__(self, locked_until: str | None = None):
        self.locked_until = locked_until
        message = f"Account is locked until {locked_until}" if locked_until else "Account is locked"
        super().__init__(message)


class AccountInactiveError(AuthError):
    """Raised when account is not active."""

    def __init__(self, message: str = "Account is not active"):
        super().__init__(message)


class PasswordExpiredError(AuthError):
    """Raised when password has expired."""

    def __init__(self, message: str = "Password has expired"):
        super().__init__(message)


class PasswordTooWeakError(AuthError):
    """Raised when password doesn't meet strength requirements."""

    def __init__(self, violations: list[str]):
        self.violations = violations
        super().__init__(f"Password too weak: {', '.join(violations)}")


class PasswordHistoryViolationError(AuthError):
    """Raised when new password was recently used."""

    def __init__(self, message: str = "Cannot reuse recent passwords"):
        super().__init__(message)


class TokenError(AuthError):
    """Base exception for token errors."""


class InvalidTokenError(TokenError):
    """Raised when token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


class TokenExpiredError(TokenError):
    """Raised when token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InsufficientPermissionsError(AuthError):
    """Raised when user lacks required permissions."""

    def __init__(self, required_permission: str):
        self.required_permission = required_permission
        super().__init__(f"Insufficient permissions: requires {required_permission}")


class SSOError(AuthError):
    """Base exception for SSO errors."""


class SSODegradedModeError(SSOError):
    """Raised when SSO service is in degraded mode."""

    def __init__(self, message: str = "SSO service is temporarily unavailable"):
        super().__init__(message)
