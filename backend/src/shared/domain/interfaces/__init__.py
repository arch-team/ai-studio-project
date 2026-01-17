"""Cross-module interfaces for Modular Monolith communication.

This module contains interface definitions that enable cross-module
communication without creating direct dependencies between modules.

Usage:
    Modules that need to call functionality from other modules should:
    1. Define the interface here
    2. Implement the interface in the providing module's infrastructure layer
    3. Inject the implementation via dependency injection

Example:
    # In training module service
    from src.shared.domain.interfaces import IQuotaChecker

    class TrainingJobService:
        def __init__(self, quota_checker: IQuotaChecker):
            self._quota_checker = quota_checker
"""

from .entity_existence_checker import IEntityExistenceChecker
from .quota_checker import IQuotaChecker

__all__ = [
    "IEntityExistenceChecker",
    "IQuotaChecker",
]
