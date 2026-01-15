"""Repository Implementations - Concrete data access.

Implements domain repository interfaces using SQLAlchemy:
- TrainingJobRepository: Training job CRUD
- DatasetRepository: Dataset CRUD
- ModelRepository: Model CRUD
- ClusterRepository: Cluster CRUD
- ResourceLimitConfigRepository: Resource limit config CRUD
- UserRepository: User CRUD
- LoginAttemptRepository: Login attempt CRUD
- PasswordHistoryRepository: Password history CRUD
"""

from src.infrastructure.persistence.repositories.login_attempt_repository_impl import (
    LoginAttemptRepository,
    get_login_attempt_repository,
)
from src.infrastructure.persistence.repositories.password_history_repository_impl import (
    PasswordHistoryRepository,
    get_password_history_repository,
)
from src.infrastructure.persistence.repositories.resource_limit_config_repository_impl import (
    ResourceLimitConfigRepository,
    get_resource_limit_config_repository,
)
from src.infrastructure.persistence.repositories.user_repository_impl import (
    UserRepository,
    get_user_repository,
)

__all__ = [
    "LoginAttemptRepository",
    "get_login_attempt_repository",
    "PasswordHistoryRepository",
    "get_password_history_repository",
    "ResourceLimitConfigRepository",
    "get_resource_limit_config_repository",
    "UserRepository",
    "get_user_repository",
]
