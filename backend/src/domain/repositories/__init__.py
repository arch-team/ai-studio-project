"""Domain Repository Interfaces - Abstract data access contracts.

Repository interfaces define the contract for data persistence
without specifying implementation details. The infrastructure
layer provides concrete implementations.
"""

from .base import IRepository
from .login_attempt_repository import ILoginAttemptRepository
from .password_history_repository import IPasswordHistoryRepository
from .resource_limit_config_repository import IResourceLimitConfigRepository
from .training_job_repository import ITrainingJobRepository
from .user_repository import IUserRepository

__all__ = [
    "IRepository",
    "ILoginAttemptRepository",
    "IPasswordHistoryRepository",
    "IResourceLimitConfigRepository",
    "ITrainingJobRepository",
    "IUserRepository",
]
