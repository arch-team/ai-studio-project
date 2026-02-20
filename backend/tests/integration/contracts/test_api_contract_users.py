"""Users API Contract 一致性验证测试。

验证 FastAPI 生成的 OpenAPI schema 与 contracts/users-api.yaml 的一致性。
确保所有 contract 定义的路径和方法在实际应用中均已实现。
"""

from typing import Any

import pytest

from tests.integration.contracts.conftest import (
    extract_contract_paths,
    load_contract_yaml,
)

# API 前缀: router.py 中 auth 挂载在 /api/v1/auth, users 挂载在 /api/v1/users
API_PREFIX = "/api/v1"


@pytest.fixture
def users_contract() -> dict[str, Any]:
    """加载 users-api.yaml contract。"""
    return load_contract_yaml("users-api.yaml")


class TestUsersContractPaths:
    """验证 users API 路径存在性。"""

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_auth_login_path(
        self, openapi_paths: dict[str, Any]
    ) -> None:
        """验证 OpenAPI schema 包含 /api/v1/auth/login 路径。"""
        # 登录路径可能有多种形式, 检查包含 login 的路径
        matching = [
            p for p in openapi_paths if "auth" in p and "login" in p
        ]
        assert len(matching) >= 1, (
            "期望 auth/login 路径在 OpenAPI schema 中存在"
        )

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_users_me_path(
        self, openapi_paths: dict[str, Any]
    ) -> None:
        """验证 OpenAPI schema 包含当前用户信息路径 (/auth/me 或 /users/me)。"""
        matching = [p for p in openapi_paths if p.endswith("/me")]
        assert len(matching) >= 1, (
            "期望 /me 路径在 OpenAPI schema 中存在"
        )

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_users_list_path(
        self, openapi_paths: dict[str, Any]
    ) -> None:
        """验证 OpenAPI schema 包含 /api/v1/users 列表路径。"""
        expected = f"{API_PREFIX}/users"
        matching = [p for p in openapi_paths if p == expected]
        assert len(matching) == 1, (
            f"期望路径 {expected} 在 OpenAPI schema 中存在"
        )

    @pytest.mark.asyncio
    async def test_openapi_schema_contains_users_detail_path(
        self, openapi_paths: dict[str, Any]
    ) -> None:
        """验证 OpenAPI schema 包含 /api/v1/users/{{user_id}} 详情路径。"""
        matching = [
            p
            for p in openapi_paths
            if p.startswith(f"{API_PREFIX}/users/{{")
            and p.endswith("}")
        ]
        assert len(matching) >= 1, (
            "期望至少有一个 users/{id} 路径"
        )


class TestUsersContractMethods:
    """验证 users API 端点支持的 HTTP 方法。"""

    @pytest.mark.asyncio
    async def test_auth_login_supports_post(
        self, openapi_paths: dict[str, Any]
    ) -> None:
        """验证 POST /auth/login 方法存在。"""
        login_path = next(
            (p for p in openapi_paths if "auth" in p and "login" in p),
            None,
        )
        assert login_path is not None, "auth/login 路径不存在"
        methods = set(openapi_paths[login_path].keys())
        assert "post" in methods, "POST /auth/login 方法缺失"

    @pytest.mark.asyncio
    async def test_users_me_supports_get(
        self, openapi_paths: dict[str, Any]
    ) -> None:
        """验证 GET /me 方法存在。"""
        me_path = next(
            (p for p in openapi_paths if p.endswith("/me")),
            None,
        )
        assert me_path is not None, "/me 路径不存在"
        methods = set(openapi_paths[me_path].keys())
        assert "get" in methods, "GET /me 方法缺失"

    @pytest.mark.asyncio
    async def test_users_list_supports_get(
        self, openapi_paths: dict[str, Any]
    ) -> None:
        """验证 GET /users 方法存在。"""
        path = f"{API_PREFIX}/users"
        assert path in openapi_paths, f"路径 {path} 不存在"
        methods = set(openapi_paths[path].keys())
        assert "get" in methods, "GET /users 方法缺失"

    @pytest.mark.asyncio
    async def test_users_detail_supports_get(
        self, openapi_paths: dict[str, Any]
    ) -> None:
        """验证 GET /users/{{user_id}} 方法存在。"""
        detail_path = next(
            (
                p
                for p in openapi_paths
                if p.startswith(f"{API_PREFIX}/users/{{")
                and p.endswith("}")
            ),
            None,
        )
        assert detail_path is not None, "users 详情路径不存在"
        methods = set(openapi_paths[detail_path].keys())
        assert "get" in methods, "GET /users/{id} 方法缺失"


class TestUsersContractConsistency:
    """验证 contract YAML 中定义的所有路径和方法在 OpenAPI schema 中均存在。"""

    @pytest.mark.asyncio
    async def test_all_contract_paths_exist_in_openapi(
        self,
        openapi_paths: dict[str, Any],
        users_contract: dict[str, Any],
    ) -> None:
        """验证 contract 中定义的所有路径在 OpenAPI schema 中均有对应。"""
        contract_paths = extract_contract_paths(users_contract)
        missing_paths: list[str] = []

        for contract_path in contract_paths:
            # users contract 路径可能挂载在 /auth 或 /users 下
            # /auth/login -> /api/v1/auth/login
            # /users/me -> /api/v1/auth/me (或 /api/v1/users/me)
            # /users -> /api/v1/users
            # /users/{user_id} -> /api/v1/users/{user_id}
            found = False

            if contract_path.startswith("/auth"):
                full_path = f"{API_PREFIX}{contract_path}"
                found = any(
                    self._paths_match(full_path, p) for p in openapi_paths
                )
            elif contract_path == "/users/me":
                # /users/me 在实际实现中可能在 /auth/me
                found = any(
                    p.endswith("/me") for p in openapi_paths
                )
            else:
                full_path = f"{API_PREFIX}{contract_path}"
                found = any(
                    self._paths_match(full_path, p) for p in openapi_paths
                )

            if not found:
                missing_paths.append(contract_path)

        assert not missing_paths, (
            f"以下 contract 路径在 OpenAPI schema 中不存在: {missing_paths}"
        )

    @pytest.mark.asyncio
    async def test_all_contract_methods_exist_in_openapi(
        self,
        openapi_paths: dict[str, Any],
        users_contract: dict[str, Any],
    ) -> None:
        """验证 contract 中定义的所有 HTTP 方法在 OpenAPI schema 中均有对应。"""
        contract_paths = extract_contract_paths(users_contract)
        missing_methods: list[str] = []

        for contract_path, methods in contract_paths.items():
            # 处理路径映射
            if contract_path.startswith("/auth"):
                full_path = f"{API_PREFIX}{contract_path}"
            elif contract_path == "/users/me":
                # 查找以 /me 结尾的路径
                openapi_path = next(
                    (p for p in openapi_paths if p.endswith("/me")),
                    None,
                )
                if openapi_path is not None:
                    openapi_methods = set(openapi_paths[openapi_path].keys())
                    for method in methods:
                        if method.lower() not in openapi_methods:
                            missing_methods.append(
                                f"{method.upper()} {contract_path}"
                            )
                continue
            else:
                full_path = f"{API_PREFIX}{contract_path}"

            openapi_path = next(
                (
                    p
                    for p in openapi_paths
                    if self._paths_match(full_path, p)
                ),
                None,
            )
            if openapi_path is None:
                continue

            openapi_methods = set(openapi_paths[openapi_path].keys())
            for method in methods:
                if method.lower() not in openapi_methods:
                    missing_methods.append(
                        f"{method.upper()} {contract_path}"
                    )

        assert not missing_methods, (
            f"以下 contract 方法在 OpenAPI schema 中不存在: {missing_methods}"
        )

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
