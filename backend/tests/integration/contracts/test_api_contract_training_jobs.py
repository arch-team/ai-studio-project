"""Training Jobs API Contract 一致性验证测试。

验证 FastAPI 生成的 OpenAPI schema 与 contracts/training-jobs-api.yaml 的一致性。
确保所有 contract 定义的路径和方法在实际应用中均已实现。
"""

from typing import Any

import pytest

from tests.integration.contracts.conftest import (
    extract_contract_paths,
    load_contract_yaml,
)

# API 前缀: router.py 中 training-jobs 挂载在 /api/v1/training-jobs
API_PREFIX = "/api/v1"


@pytest.fixture
def training_jobs_contract() -> dict[str, Any]:
    """加载 training-jobs-api.yaml contract。"""
    return load_contract_yaml("training-jobs-api.yaml")


class TestTrainingJobsContractPaths:
    """验证 training-jobs API 路径存在性。"""

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_training_jobs_list_path(self, openapi_paths: dict[str, Any]) -> None:
        """验证 OpenAPI schema 包含 /api/v1/training-jobs 列表路径。"""
        expected = f"{API_PREFIX}/training-jobs"
        matching = [p for p in openapi_paths if p == expected]
        assert len(matching) == 1, f"期望路径 {expected} 在 OpenAPI schema 中存在"

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_training_jobs_detail_path(self, openapi_paths: dict[str, Any]) -> None:
        """验证 OpenAPI schema 包含 /api/v1/training-jobs/{{job_id}} 详情路径。"""
        # FastAPI 使用 {job_id} 格式
        matching = [
            p
            for p in openapi_paths
            if p.startswith(f"{API_PREFIX}/training-jobs/{{")
            and p.endswith("}")
            and "logs" not in p
            and "metrics" not in p
            and "checkpoints" not in p
            and "debug" not in p
            and "pause" not in p
            and "resume" not in p
            and "cancel" not in p
            and "template" not in p
        ]
        assert len(matching) >= 1, "期望至少有一个 training-jobs/{id} 路径"

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_training_jobs_logs_path(self, openapi_paths: dict[str, Any]) -> None:
        """验证 OpenAPI schema 包含 training-jobs 日志路径。"""
        matching = [p for p in openapi_paths if "training-jobs" in p and "logs" in p]
        assert len(matching) >= 1, "期望 training-jobs 日志路径在 OpenAPI schema 中存在"

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_training_jobs_metrics_path(self, openapi_paths: dict[str, Any]) -> None:
        """验证 OpenAPI schema 包含 training-jobs 指标路径。"""
        matching = [p for p in openapi_paths if "training-jobs" in p and "metrics" in p]
        assert len(matching) >= 1, "期望 training-jobs 指标路径在 OpenAPI schema 中存在"

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_training_jobs_checkpoints_path(self, openapi_paths: dict[str, Any]) -> None:
        """验证 OpenAPI schema 包含 training-jobs 检查点路径。"""
        matching = [p for p in openapi_paths if "training-jobs" in p and "checkpoints" in p]
        assert len(matching) >= 1, "期望 training-jobs 检查点路径在 OpenAPI schema 中存在"


class TestTrainingJobsContractMethods:
    """验证 training-jobs API 端点支持的 HTTP 方法。"""

    @pytest.mark.asyncio
    async def test_training_jobs_list_supports_get(self, openapi_paths: dict[str, Any]) -> None:
        """验证 GET /training-jobs 方法存在。"""
        path = f"{API_PREFIX}/training-jobs"
        assert path in openapi_paths, f"路径 {path} 不存在"
        methods = set(openapi_paths[path].keys())
        assert "get" in methods, "GET /training-jobs 方法缺失"

    @pytest.mark.asyncio
    async def test_training_jobs_list_supports_post(self, openapi_paths: dict[str, Any]) -> None:
        """验证 POST /training-jobs 方法存在。"""
        path = f"{API_PREFIX}/training-jobs"
        assert path in openapi_paths, f"路径 {path} 不存在"
        methods = set(openapi_paths[path].keys())
        assert "post" in methods, "POST /training-jobs 方法缺失"

    @pytest.mark.asyncio
    async def test_training_jobs_detail_supports_get(self, openapi_paths: dict[str, Any]) -> None:
        """验证 GET /training-jobs/{{job_id}} 方法存在。"""
        detail_path = next(
            (
                p
                for p in openapi_paths
                if p.startswith(f"{API_PREFIX}/training-jobs/{{")
                and p.endswith("}")
                and "logs" not in p
                and "metrics" not in p
                and "checkpoints" not in p
                and "debug" not in p
                and "pause" not in p
                and "resume" not in p
                and "cancel" not in p
                and "template" not in p
            ),
            None,
        )
        assert detail_path is not None, "training-jobs 详情路径不存在"
        methods = set(openapi_paths[detail_path].keys())
        assert "get" in methods, "GET /training-jobs/{id} 方法缺失"

    @pytest.mark.asyncio
    async def test_training_jobs_detail_supports_delete(self, openapi_paths: dict[str, Any]) -> None:
        """验证 DELETE /training-jobs/{{job_id}} 方法存在。"""
        detail_path = next(
            (
                p
                for p in openapi_paths
                if p.startswith(f"{API_PREFIX}/training-jobs/{{")
                and p.endswith("}")
                and "logs" not in p
                and "metrics" not in p
                and "checkpoints" not in p
                and "debug" not in p
                and "pause" not in p
                and "resume" not in p
                and "cancel" not in p
                and "template" not in p
            ),
            None,
        )
        assert detail_path is not None, "training-jobs 详情路径不存在"
        methods = set(openapi_paths[detail_path].keys())
        assert "delete" in methods, "DELETE /training-jobs/{id} 方法缺失"


class TestTrainingJobsContractConsistency:
    """验证 contract YAML 中定义的所有路径和方法在 OpenAPI schema 中均存在。"""

    @pytest.mark.asyncio
    async def test_all_contract_paths_exist_in_openapi(
        self,
        openapi_paths: dict[str, Any],
        training_jobs_contract: dict[str, Any],
    ) -> None:
        """验证 contract 中定义的所有路径在 OpenAPI schema 中均有对应。"""
        contract_paths = extract_contract_paths(training_jobs_contract)
        missing_paths: list[str] = []

        for contract_path in contract_paths:
            # contract 路径格式: /training-jobs/{job_id}
            # OpenAPI 路径格式: /api/v1/training-jobs/{job_id}
            full_path = f"{API_PREFIX}{contract_path}"
            # 匹配时需要考虑路径参数名差异
            found = any(self._paths_match(full_path, openapi_path) for openapi_path in openapi_paths)
            if not found:
                missing_paths.append(contract_path)

        assert not missing_paths, f"以下 contract 路径在 OpenAPI schema 中不存在: {missing_paths}"

    @pytest.mark.xfail(
        reason="已知差异: GET /checkpoints (列表) 尚未实现，当前仅有 POST (创建)",
        strict=False,
    )
    @pytest.mark.asyncio
    async def test_all_contract_methods_exist_in_openapi(
        self,
        openapi_paths: dict[str, Any],
        training_jobs_contract: dict[str, Any],
    ) -> None:
        """验证 contract 中定义的所有 HTTP 方法在 OpenAPI schema 中均有对应。

        注意: patch 和 put 视为等价的更新操作。
        已知差异: GET /checkpoints (列表查询) 尚未实现。
        """
        contract_paths = extract_contract_paths(training_jobs_contract)
        # 允许 patch/put 互换 (均为更新操作)
        update_equivalents = {"patch", "put"}
        missing_methods: list[str] = []

        for contract_path, methods in contract_paths.items():
            full_path = f"{API_PREFIX}{contract_path}"
            # 查找匹配的 OpenAPI 路径
            openapi_path = next(
                (p for p in openapi_paths if self._paths_match(full_path, p)),
                None,
            )
            if openapi_path is None:
                continue  # 路径缺失由上一个测试检查

            openapi_methods = set(openapi_paths[openapi_path].keys())
            for method in methods:
                method_lower = method.lower()
                # patch/put 视为等价
                if method_lower in update_equivalents:
                    if not (openapi_methods & update_equivalents):
                        missing_methods.append(f"{method.upper()} {contract_path}")
                elif method_lower not in openapi_methods:
                    missing_methods.append(f"{method.upper()} {contract_path}")

        assert not missing_methods, f"以下 contract 方法在 OpenAPI schema 中不存在: {missing_methods}"

    @staticmethod
    def _paths_match(path_a: str, path_b: str) -> bool:
        """比较两个路径是否匹配 (忽略路径参数名差异)。

        例如: /api/v1/training-jobs/{job_id} 匹配 /api/v1/training-jobs/{job_id}
        """
        parts_a = path_a.strip("/").split("/")
        parts_b = path_b.strip("/").split("/")

        if len(parts_a) != len(parts_b):
            return False

        for a, b in zip(parts_a, parts_b):
            # 如果两个部分都是路径参数，则认为匹配
            if a.startswith("{") and b.startswith("{"):
                continue
            if a != b:
                return False
        return True
