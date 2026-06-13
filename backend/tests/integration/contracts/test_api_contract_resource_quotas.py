"""Resource Quotas API Contract 一致性验证测试。

验证 FastAPI 生成的 OpenAPI schema 与 contracts/resource-quotas-api.yaml 的一致性。
确保所有 contract 定义的路径和方法在实际应用中均已实现。
"""

from typing import Any

import pytest

from tests.integration.contracts.conftest import (
    extract_contract_paths,
    load_contract_yaml,
)

# API 前缀: router.py 中 resource-quotas 挂载在 /api/v1/resource-quotas
API_PREFIX = "/api/v1"


@pytest.fixture
def resource_quotas_contract() -> dict[str, Any]:
    """加载 resource-quotas-api.yaml contract。"""
    return load_contract_yaml("resource-quotas-api.yaml")


class TestResourceQuotasContractPaths:
    """验证 resource-quotas API 路径存在性。"""

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_resource_quotas_list_path(self, openapi_paths: dict[str, Any]) -> None:
        """验证 OpenAPI schema 包含 /api/v1/resource-quotas 列表路径。"""
        expected = f"{API_PREFIX}/resource-quotas"
        matching = [p for p in openapi_paths if p == expected]
        assert len(matching) == 1, f"期望路径 {expected} 在 OpenAPI schema 中存在"

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_resource_quotas_detail_path(self, openapi_paths: dict[str, Any]) -> None:
        """验证 OpenAPI schema 包含 /api/v1/resource-quotas/{{quota_id}} 详情路径。"""
        matching = [
            p
            for p in openapi_paths
            if p.startswith(f"{API_PREFIX}/resource-quotas/{{") and p.endswith("}") and "usage" not in p
        ]
        assert len(matching) >= 1, "期望至少有一个 resource-quotas/{id} 路径"


class TestResourceQuotasContractMethods:
    """验证 resource-quotas API 端点支持的 HTTP 方法。"""

    @pytest.mark.asyncio
    async def test_resource_quotas_list_supports_get(self, openapi_paths: dict[str, Any]) -> None:
        """验证 GET /resource-quotas 方法存在。"""
        path = f"{API_PREFIX}/resource-quotas"
        assert path in openapi_paths, f"路径 {path} 不存在"
        methods = set(openapi_paths[path].keys())
        assert "get" in methods, "GET /resource-quotas 方法缺失"

    @pytest.mark.asyncio
    async def test_resource_quotas_list_supports_post(self, openapi_paths: dict[str, Any]) -> None:
        """验证 POST /resource-quotas 方法存在。"""
        path = f"{API_PREFIX}/resource-quotas"
        assert path in openapi_paths, f"路径 {path} 不存在"
        methods = set(openapi_paths[path].keys())
        assert "post" in methods, "POST /resource-quotas 方法缺失"

    @pytest.mark.asyncio
    async def test_resource_quotas_detail_supports_get(self, openapi_paths: dict[str, Any]) -> None:
        """验证 GET /resource-quotas/{{quota_id}} 方法存在。"""
        detail_path = next(
            (
                p
                for p in openapi_paths
                if p.startswith(f"{API_PREFIX}/resource-quotas/{{") and p.endswith("}") and "usage" not in p
            ),
            None,
        )
        assert detail_path is not None, "resource-quotas 详情路径不存在"
        methods = set(openapi_paths[detail_path].keys())
        assert "get" in methods, "GET /resource-quotas/{id} 方法缺失"


class TestResourceQuotasContractConsistency:
    """验证 contract YAML 中定义的所有路径和方法在 OpenAPI schema 中均存在。"""

    @pytest.mark.xfail(
        reason="已知差异: /resource-quotas/{quota_id}/usage 端点尚未实现",
        strict=False,
    )
    @pytest.mark.asyncio
    async def test_all_contract_paths_exist_in_openapi(
        self,
        openapi_paths: dict[str, Any],
        resource_quotas_contract: dict[str, Any],
    ) -> None:
        """验证 contract 中定义的所有路径在 OpenAPI schema 中均有对应。

        已知差异: /resource-quotas/{quota_id}/usage 端点尚未实现。
        """
        contract_paths = extract_contract_paths(resource_quotas_contract)
        missing_paths: list[str] = []

        for contract_path in contract_paths:
            full_path = f"{API_PREFIX}{contract_path}"
            found = any(self._paths_match(full_path, openapi_path) for openapi_path in openapi_paths)
            if not found:
                missing_paths.append(contract_path)

        assert not missing_paths, f"以下 contract 路径在 OpenAPI schema 中不存在: {missing_paths}"

    @pytest.mark.asyncio
    async def test_all_contract_methods_exist_in_openapi(
        self,
        openapi_paths: dict[str, Any],
        resource_quotas_contract: dict[str, Any],
    ) -> None:
        """验证 contract 中定义的所有 HTTP 方法在 OpenAPI schema 中均有对应。"""
        contract_paths = extract_contract_paths(resource_quotas_contract)
        missing_methods: list[str] = []

        for contract_path, methods in contract_paths.items():
            full_path = f"{API_PREFIX}{contract_path}"
            openapi_path = next(
                (p for p in openapi_paths if self._paths_match(full_path, p)),
                None,
            )
            if openapi_path is None:
                continue

            openapi_methods = set(openapi_paths[openapi_path].keys())
            for method in methods:
                if method.lower() not in openapi_methods:
                    missing_methods.append(f"{method.upper()} {contract_path}")

        assert not missing_methods, f"以下 contract 方法在 OpenAPI schema 中不存在: {missing_methods}"

    @staticmethod
    def _paths_match(path_a: str, path_b: str) -> bool:
        """比较两个路径是否匹配 (忽略路径参数名差异)。"""
        parts_a = path_a.strip("/").split("/")
        parts_b = path_b.strip("/").split("/")

        if len(parts_a) != len(parts_b):
            return False

        for a, b in zip(parts_a, parts_b):
            if a.startswith("{") and b.startswith("{"):
                continue
            if a != b:
                return False
        return True
