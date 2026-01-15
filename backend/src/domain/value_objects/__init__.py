"""Domain Value Objects - Immutable objects defined by their attributes.

Value objects encapsulate domain concepts without identity:
- ResourceConfig: CPU, memory, GPU configuration
- JobStatus: Training job state enumeration
- StoragePath: S3/FSx path with validation
- TrainingConfig: Hyperparameters and training settings
- UserStatus, UserRole, AuthType: User-related enumerations
"""

from src.domain.value_objects.user_enums import AuthType, UserRole, UserStatus

__all__ = ["AuthType", "UserRole", "UserStatus"]
