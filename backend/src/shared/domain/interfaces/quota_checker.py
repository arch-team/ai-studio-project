"""Quota Checker Interface - Cross-module interface for quota validation.

This interface enables the training module to check resource quotas
without directly depending on the quotas module.

Implementation:
    The quotas module provides QuotaCheckerImpl in its infrastructure layer.

Usage in training module:
    from src.shared.domain.interfaces import IQuotaChecker

    class TrainingJobService:
        def __init__(self, quota_checker: IQuotaChecker):
            self._quota_checker = quota_checker

        async def submit_job(self, job: TrainingJob) -> TrainingJob:
            # Check quota before submission
            has_quota = await self._quota_checker.check_quota(
                user_id=job.owner_id,
                resource_type="gpu",
                amount=job.gpu_count,
            )
            if not has_quota:
                raise ResourceQuotaExceededError(...)
"""

from abc import ABC, abstractmethod


class IQuotaChecker(ABC):
    """Interface for checking and consuming resource quotas.

    This interface decouples the training module from the quotas module,
    allowing cross-module quota validation without direct dependencies.
    """

    @abstractmethod
    async def check_quota(
        self,
        user_id: int,
        resource_type: str,
        amount: int,
    ) -> bool:
        """Check if user has sufficient quota for the requested resources.

        Args:
            user_id: The user requesting resources.
            resource_type: Type of resource (e.g., "gpu", "cpu", "memory").
            amount: Amount of resource requested.

        Returns:
            True if quota is available, False otherwise.
        """
        pass

    @abstractmethod
    async def consume_quota(
        self,
        user_id: int,
        resource_type: str,
        amount: int,
    ) -> None:
        """Consume quota for the specified resources.

        Args:
            user_id: The user consuming resources.
            resource_type: Type of resource being consumed.
            amount: Amount of resource to consume.

        Raises:
            ResourceQuotaExceededError: If insufficient quota available.
        """
        pass

    @abstractmethod
    async def release_quota(
        self,
        user_id: int,
        resource_type: str,
        amount: int,
    ) -> None:
        """Release previously consumed quota.

        Args:
            user_id: The user releasing resources.
            resource_type: Type of resource being released.
            amount: Amount of resource to release.
        """
        pass

    @abstractmethod
    async def get_available_quota(
        self,
        user_id: int,
        resource_type: str,
    ) -> int:
        """Get the available quota for a user and resource type.

        Args:
            user_id: The user to check.
            resource_type: Type of resource to check.

        Returns:
            Available quota amount.
        """
        pass
