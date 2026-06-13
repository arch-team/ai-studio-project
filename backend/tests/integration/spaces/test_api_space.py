"""Space API 端点集成测试 - 依赖数据库，无 DB 时优雅跳过。

测试 POST /spaces 端点支持 backend="hyperpod" 字段。
"""

import os
from typing import Any

import pytest
from httpx import AsyncClient


@pytest.fixture
def create_studio_space_request() -> dict[str, Any]:
    """Studio Space 创建请求（默认 backend）。"""
    return {
        "space_name": "test-studio-space",
        "instance_type": "ml.g5.xlarge",
        "space_type": "jupyter",
        "storage_size_gb": 20,
    }


@pytest.fixture
def create_hyperpod_space_request() -> dict[str, Any]:
    """HyperPod Space 创建请求（backend="hyperpod"）。"""
    return {
        "space_name": "test-hyperpod-space",
        "instance_type": "ml.g5.2xlarge",
        "space_type": "vscode",
        "storage_size_gb": 50,
        "backend": "hyperpod",
    }


class TestCreateSpaceEndpointBackend:
    """测试 POST /spaces 端点的 backend 字段支持。"""

    @pytest.mark.asyncio
    async def test_create_space_studio_backend_default(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        create_studio_space_request: dict[str, Any],
    ) -> None:
        """创建 Studio Space（默认 backend）返回 201 且 backend="studio"。"""
        if not os.getenv("DATABASE_URL"):
            pytest.skip("No database available - skipping integration test")

        # Mock SpaceService to avoid real SageMaker/K8s calls
        from unittest.mock import AsyncMock, MagicMock

        from src.modules.spaces.domain.entities import Space
        from src.modules.spaces.domain.value_objects import SpaceBackend, SpaceInstanceType, SpaceStatus, SpaceType

        mock_space = Space(
            id="space-studio-123",
            space_name="test-studio-space",
            owner_id=1,
            instance_type=SpaceInstanceType.ML_G5_XLARGE,
            space_type=SpaceType.JUPYTER,
            backend=SpaceBackend.STUDIO,
            storage_size_gb=20,
            status=SpaceStatus.PENDING,
        )

        mock_service = MagicMock()
        mock_service.create_space = AsyncMock(return_value=mock_space)

        from src.main import app

        async def get_mock_space_service() -> MagicMock:
            return mock_service

        from src.modules.spaces.api.dependencies import get_space_service

        app.dependency_overrides[get_space_service] = get_mock_space_service

        try:
            response = await client.post(
                "/api/v1/spaces",
                json=create_studio_space_request,
                headers=engineer_auth_headers,
            )

            assert response.status_code == 201
            data = response.json()
            assert data["backend"] == "studio"
            assert data["space_name"] == "test-studio-space"
            assert data["namespace"] is None
            assert data["queue_name"] is None
            assert data["workspace_template"] is None
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_space_hyperpod_backend(
        self,
        client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        create_hyperpod_space_request: dict[str, Any],
    ) -> None:
        """创建 HyperPod Space（backend="hyperpod"）返回 201 且 backend="hyperpod"。"""
        if not os.getenv("DATABASE_URL"):
            pytest.skip("No database available - skipping integration test")

        # Mock SpaceService to avoid real K8s calls
        from unittest.mock import AsyncMock, MagicMock

        from src.modules.spaces.domain.entities import Space
        from src.modules.spaces.domain.value_objects import SpaceBackend, SpaceInstanceType, SpaceStatus, SpaceType

        mock_space = Space(
            id="space-hyperpod-456",
            space_name="test-hyperpod-space",
            owner_id=1,
            instance_type=SpaceInstanceType.ML_G5_2XLARGE,
            space_type=SpaceType.VSCODE,
            backend=SpaceBackend.HYPERPOD,
            namespace="default",
            queue_name="gpu-queue",
            workspace_template="vscode-template",
            storage_size_gb=50,
            status=SpaceStatus.PENDING,
        )

        mock_service = MagicMock()
        mock_service.create_space = AsyncMock(return_value=mock_space)

        from src.main import app

        async def get_mock_space_service() -> MagicMock:
            return mock_service

        from src.modules.spaces.api.dependencies import get_space_service

        app.dependency_overrides[get_space_service] = get_mock_space_service

        try:
            response = await client.post(
                "/api/v1/spaces",
                json=create_hyperpod_space_request,
                headers=engineer_auth_headers,
            )

            assert response.status_code == 201
            data = response.json()
            assert data["backend"] == "hyperpod"
            assert data["space_name"] == "test-hyperpod-space"
            # HyperPod 字段由 Service 层根据 backend 填充
            # API 层只需确保能接收和返回这些字段
        finally:
            app.dependency_overrides.clear()
