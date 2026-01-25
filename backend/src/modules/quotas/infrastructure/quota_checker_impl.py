"""QuotaCheckerImpl - Implementation of IQuotaChecker interface (CE-01-05).

This implementation provides resource quota validation for the training module
without creating a direct dependency on the quotas module.
"""

from src.modules.quotas.domain.repositories import IResourceQuotaRepository
from src.shared.domain.exceptions import ResourceQuotaExceededError
from src.shared.domain.interfaces import IQuotaChecker


class QuotaCheckerImpl(IQuotaChecker):
    """Implementation of IQuotaChecker for resource quota validation.

    Uses ResourceQuota repository to check and manage quota consumption.
    """

    # Instance type to GPU count mapping
    INSTANCE_GPU_COUNTS: dict[str, int] = {
        "ml.p4d.24xlarge": 8,
        "ml.p4de.24xlarge": 8,
        "ml.p3.2xlarge": 1,
        "ml.p3.8xlarge": 4,
        "ml.p3.16xlarge": 8,
        "ml.g4dn.xlarge": 1,
        "ml.g4dn.2xlarge": 1,
        "ml.g4dn.4xlarge": 1,
        "ml.g4dn.8xlarge": 1,
        "ml.g4dn.12xlarge": 4,
        "ml.g4dn.16xlarge": 1,
        "ml.g5.xlarge": 1,
        "ml.g5.2xlarge": 1,
        "ml.g5.4xlarge": 1,
        "ml.g5.8xlarge": 1,
        "ml.g5.12xlarge": 4,
        "ml.g5.16xlarge": 1,
        "ml.g5.24xlarge": 4,
        "ml.g5.48xlarge": 8,
    }

    def __init__(self, quota_repository: IResourceQuotaRepository):
        """Initialize with quota repository.

        Args:
            quota_repository: Repository for ResourceQuota access.
        """
        self._repository = quota_repository
        # In-memory tracking of consumed quotas (should be replaced with persistent storage)
        self._consumed_quotas: dict[int, dict[str, int]] = {}

    async def check_quota(
        self,
        user_id: int,
        resource_type: str,
        amount: int,
    ) -> bool:
        """Check if user has sufficient quota for the requested resources."""
        # Get user's quota (by name pattern 'user-{user_id}-quota')
        quota_name = f"user-{user_id}-quota"
        quota = await self._repository.get_by_name(quota_name)

        if quota is None or not quota.is_active():
            # No quota defined or inactive - check system default
            default_quota = await self._repository.get_by_name("default-quota")
            if default_quota is None or not default_quota.is_active():
                return False
            quota = default_quota

        # Get current consumed amount
        consumed = self._consumed_quotas.get(user_id, {}).get(resource_type, 0)

        # Check resource type specific limits
        if resource_type == "gpu":
            return (consumed + amount) <= quota.max_gpu_count
        elif resource_type == "cpu":
            return (consumed + amount) <= quota.max_cpu_cores
        elif resource_type == "memory":
            return (consumed + amount) <= quota.max_memory_gb
        else:
            return True  # Unknown resource type, allow by default

    async def consume_quota(
        self,
        user_id: int,
        resource_type: str,
        amount: int,
    ) -> None:
        """Consume quota for the specified resources."""
        # Check quota first
        has_quota = await self.check_quota(user_id, resource_type, amount)
        if not has_quota:
            available = await self.get_available_quota(user_id, resource_type)
            raise ResourceQuotaExceededError(
                resource_type=resource_type,
                limit=available,
                requested=amount,
            )

        # Update consumed quota
        if user_id not in self._consumed_quotas:
            self._consumed_quotas[user_id] = {}

        current = self._consumed_quotas[user_id].get(resource_type, 0)
        self._consumed_quotas[user_id][resource_type] = current + amount

    async def release_quota(
        self,
        user_id: int,
        resource_type: str,
        amount: int,
    ) -> None:
        """Release previously consumed quota."""
        if user_id not in self._consumed_quotas:
            return

        current = self._consumed_quotas[user_id].get(resource_type, 0)
        self._consumed_quotas[user_id][resource_type] = max(0, current - amount)

    async def get_available_quota(
        self,
        user_id: int,
        resource_type: str,
    ) -> int:
        """Get the available quota for a user and resource type."""
        # Get user's quota
        quota_name = f"user-{user_id}-quota"
        quota = await self._repository.get_by_name(quota_name)

        if quota is None or not quota.is_active():
            default_quota = await self._repository.get_by_name("default-quota")
            if default_quota is None or not default_quota.is_active():
                return 0
            quota = default_quota

        # Get total limit for resource type
        if resource_type == "gpu":
            limit = quota.max_gpu_count
        elif resource_type == "cpu":
            limit = quota.max_cpu_cores
        elif resource_type == "memory":
            limit = quota.max_memory_gb
        else:
            return 0

        # Subtract consumed amount
        consumed = self._consumed_quotas.get(user_id, {}).get(resource_type, 0)
        return max(0, limit - consumed)

    def get_gpu_count_for_instance(self, instance_type: str) -> int:
        """Get the number of GPUs for an instance type.

        Args:
            instance_type: AWS instance type (e.g., 'ml.p4d.24xlarge').

        Returns:
            Number of GPUs for the instance type, or 1 if unknown.
        """
        return self.INSTANCE_GPU_COUNTS.get(instance_type, 1)
