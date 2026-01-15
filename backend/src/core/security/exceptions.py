"""Security Exceptions - Authentication and authorization errors."""


class SecurityError(Exception):
    """Base class for security-related errors."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code or "SECURITY_ERROR"
        super().__init__(self.message)


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTHENTICATION_FAILED")


class UserNotFoundError(SecurityError):
    """Raised when user is not found (for enable/disable account)."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User with id '{user_id}' not found", code="USER_NOT_FOUND")


class InvalidCredentialsError(SecurityError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message, code="INVALID_CREDENTIALS")


class AccountValidationError(SecurityError):
    """Raised when account validation fails (for create account)."""

    def __init__(self, message: str):
        super().__init__(message, code="ACCOUNT_VALIDATION_FAILED")


class TokenExpiredError(SecurityError):
    """Raised when a token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, code="TOKEN_EXPIRED")


class InvalidTokenError(SecurityError):
    """Raised when a token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, code="INVALID_TOKEN")


class AccountLockedError(SecurityError):
    """Raised when an account is locked due to too many failed login attempts."""

    def __init__(
        self, message: str = "Account is locked", locked_until: str | None = None
    ):
        self.locked_until = locked_until
        super().__init__(message, code="ACCOUNT_LOCKED")


class PasswordTooWeakError(SecurityError):
    """Raised when a password does not meet strength requirements."""

    def __init__(self, violations: list[str]):
        self.violations = violations
        message = "Password does not meet requirements: " + "; ".join(violations)
        super().__init__(message, code="PASSWORD_TOO_WEAK")


class PasswordHistoryViolationError(SecurityError):
    """Raised when a password was recently used."""

    def __init__(self, message: str = "Cannot reuse recent passwords"):
        super().__init__(message, code="PASSWORD_HISTORY_VIOLATION")


class PasswordExpiredError(SecurityError):
    """Raised when a password has expired."""

    def __init__(self, message: str = "Password has expired"):
        super().__init__(message, code="PASSWORD_EXPIRED")


class InsufficientPermissionsError(SecurityError):
    """Raised when a user lacks required permissions."""

    def __init__(self, required_permission: str):
        self.required_permission = required_permission
        message = f"Insufficient permissions: requires {required_permission}"
        super().__init__(message, code="INSUFFICIENT_PERMISSIONS")


class SSOError(SecurityError):
    """Raised when SSO authentication fails."""

    def __init__(
        self, message: str = "SSO authentication failed", degraded: bool = False
    ):
        self.degraded = degraded
        super().__init__(message, code="SSO_ERROR")


class SSODegradedModeError(SSOError):
    """Raised when SSO is in degraded mode."""

    def __init__(self, message: str = "SSO service is temporarily unavailable"):
        super().__init__(message, degraded=True)
