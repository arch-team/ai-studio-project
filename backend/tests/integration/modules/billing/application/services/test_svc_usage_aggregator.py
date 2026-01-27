"""UsageAggregatorService 集成测试 - 资源使用聚合查询服务。

测试策略:
1. 使用真实数据库连接进行聚合查询测试
2. 测试基本聚合功能 (不存在用户、无效参数等)
3. 测试返回值类型正确性

注意: 由于涉及真实数据库，完整的数据准备测试放在 E2E 测试中。

文件命名: test_svc_usage_aggregator.py (svc = 应用服务测试)
"""

from datetime import timedelta
from decimal import Decimal

import pytest

from src.modules.billing.application.services.usage_aggregator import UsageAggregatorService
from src.shared.infrastructure.database import get_db
from src.shared.utils import utc_now


class TestUsageAggregatorServiceIntegration:
    """UsageAggregatorService 集成测试。"""

    @pytest.mark.asyncio
    async def test_aggregate_by_user_with_nonexistent_user_should_return_zeros(self):
        """测试不存在的用户应返回零值。"""
        # Arrange
        async for session in get_db():
            service = UsageAggregatorService(session=session)

            # Act
            result = await service.aggregate_by_user(user_id=999999)

            # Assert
            assert result is not None
            assert result.user_id == 999999
            assert result.total_gpu_hours == Decimal("0")
            assert result.total_cost_usd == Decimal("0")
            assert result.total_storage_bytes == 0
            assert result.total_training_jobs == 0

    @pytest.mark.asyncio
    async def test_aggregate_by_time_period_with_invalid_period_should_raise_error(self):
        """测试无效的时间维度应抛出错误。"""
        # Arrange
        async for session in get_db():
            service = UsageAggregatorService(session=session)
            start_date = utc_now() - timedelta(days=7)
            end_date = utc_now()

            # Act & Assert
            with pytest.raises(ValueError, match="Invalid period"):
                await service.aggregate_by_time_period(
                    user_id=1, start_date=start_date, end_date=end_date, period="invalid"  # type: ignore
                )

    @pytest.mark.asyncio
    async def test_aggregate_all_users_returns_list(self):
        """测试聚合所有用户应返回列表 (可能为空)。"""
        # Arrange
        async for session in get_db():
            service = UsageAggregatorService(session=session)

            # Act
            result = await service.aggregate_all_users()

            # Assert
            assert isinstance(result, list)
            # 不断言具体长度，因为数据库中的数据可能不同
