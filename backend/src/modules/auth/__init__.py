"""Auth module - Authentication, authorization, and user management.

This module provides:
- User authentication (local and SSO)
- Password management
- Role-based access control (RBAC)
- User account management
"""

from .api import (
    CurrentUser,
    router,
)
from .application import (
    AccountService,
    AuthResult,
    AuthService,
    PasswordService,
    RBACService,
    TokenPair,
    get_rbac_service,
)
from .domain import (
    AuthType,
    ILoginAttemptRepository,
    IPasswordHistoryRepository,
    IUserRepository,
    LoginAttempt,
    PasswordHistory,
    Permission,
    User,
    UserRole,
    UserStatus,
)
from .infrastructure import (
    LoginAttemptModel,
    LoginAttemptRepositoryImpl,
    PasswordHistoryModel,
    PasswordHistoryRepositoryImpl,
    UserModel,
    UserRepositoryImpl,
)

__all__ = [
    # Router
    "router",
    # Current User
    "CurrentUser",
    # Services
    "AuthService",
    "AuthResult",
    "TokenPair",
    "PasswordService",
    "AccountService",
    "RBACService",
    "get_rbac_service",
    # Entities
    "User",
    "LoginAttempt",
    "PasswordHistory",
    # Value Objects
    "UserStatus",
    "UserRole",
    "AuthType",
    "Permission",
    # Repository Interfaces
    "IUserRepository",
    "ILoginAttemptRepository",
    "IPasswordHistoryRepository",
    # Models
    "UserModel",
    "LoginAttemptModel",
    "PasswordHistoryModel",
    # Repository Implementations
    "UserRepositoryImpl",
    "LoginAttemptRepositoryImpl",
    "PasswordHistoryRepositoryImpl",
]
