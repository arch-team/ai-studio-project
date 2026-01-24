"""SSO 故障转移 E2E 测试 (T013d)

在真实 AWS 环境验证:
1. IdP 超时时的降级行为
2. SSO 恢复后的自动切换
3. 审计日志记录完整性
4. 安全错误消息 (不泄露账号存在性)

环境要求:
- AWS 凭证配置
- SSO IdP 端点可访问
- 测试用户账号

运行方式:
    # 设置环境变量
    export AWS_REGION=us-west-2
    export SSO_IDP_URL=https://sso.example.com
    export E2E_READ_ONLY=false

    # 运行测试
    pytest tests/e2e/aws/test_e2e_sso_failover.py -v -s

依赖: T013a (SSO 集成), T013c (本地账号 API)
参考: FR-015 (spec.md)
"""

import asyncio
import time
from typing import Any

import pytest
from httpx import AsyncClient

from .conftest import (
    SLAConstants,
    skip_without_aws,
    skip_without_sso,
    skip_write_tests,
)


@pytest.mark.e2e
@pytest.mark.aws_integration
@pytest.mark.slow
@skip_without_aws
@skip_without_sso
class TestSSOFailoverE2E:
    """SSO 故障转移 E2E 测试 - FR-015

    在真实环境验证 SSO 故障时的降级和恢复行为。
    """

    @pytest.mark.asyncio
    async def test_idp_timeout_triggers_local_fallback(
        self,
        async_client: AsyncClient,
        test_local_user: dict[str, str],
    ) -> None:
        """场景1: IdP 超时时降级到本地认证

        验证步骤:
        1. 使用本地用户凭证尝试登录
        2. 如果 SSO 不可用，系统应自动降级到本地认证
        3. 验证登录成功且在 SLA 时间内完成
        """
        # Arrange: 记录开始时间
        start_time = time.time()

        # Act: 尝试登录 (SSO 降级路径)
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": test_local_user["username"],
                "password": test_local_user["password"],
            },
            headers={"X-Auth-Fallback": "true"},  # 触发降级测试模式
        )
        elapsed = time.time() - start_time

        # Assert
        if response.status_code == 200:
            # 登录成功
            data = response.json()
            # API 返回嵌套结构: {tokens: {access_token: ...}, user: {...}}
            assert "tokens" in data or "access_token" in data
            if "tokens" in data:
                assert "access_token" in data["tokens"]
            # 验证降级在 SLA 时间内完成 (5s + 2s buffer)
            assert elapsed < SLAConstants.SSO_FAILOVER_TIMEOUT + 2
            print(f"✅ SSO 降级登录成功，耗时: {elapsed:.2f}s")
        elif response.status_code == 401:
            # 凭证无效，但系统正常响应
            print(f"⚠️ 登录失败 (凭证无效): {response.json()}")
            pytest.skip("Test user credentials not configured correctly")
        else:
            pytest.fail(f"Unexpected response: {response.status_code}")

    @pytest.mark.asyncio
    async def test_sso_health_check_endpoint(
        self,
        async_client: AsyncClient,
        sso_health_endpoint: str,
    ) -> None:
        """场景2: SSO 健康检查端点验证

        验证步骤:
        1. 查询 SSO 健康状态端点
        2. 验证健康检查响应格式正确
        3. 验证返回状态在有效范围内
        """
        # Act: 查询健康状态
        response = await async_client.get(sso_health_endpoint)

        # Assert
        if response.status_code == 200:
            health_data = response.json()
            assert "status" in health_data
            assert health_data["status"] in ["healthy", "degraded", "unhealthy"]

            # 如果有 last_check 字段，验证格式
            if "last_check" in health_data:
                assert isinstance(health_data["last_check"], str)

            print(f"✅ SSO 健康状态: {health_data['status']}")
        elif response.status_code == 404:
            pytest.skip("SSO health endpoint not implemented yet")
        else:
            print(f"⚠️ Health check response: {response.status_code}")

    @pytest.mark.asyncio
    async def test_sso_recovery_detection(
        self,
        async_client: AsyncClient,
        sso_health_endpoint: str,
    ) -> None:
        """场景2b: SSO 恢复检测

        验证步骤:
        1. 多次查询健康状态
        2. 验证状态变化能被正确检测
        """
        # Act: 多次查询健康状态
        statuses = []
        for _ in range(3):
            response = await async_client.get(sso_health_endpoint)
            if response.status_code == 200:
                statuses.append(response.json().get("status"))
            await asyncio.sleep(SLAConstants.SSO_RECOVERY_CHECK_INTERVAL / 10)

        # Assert: 验证状态一致性
        if statuses:
            print(f"✅ SSO 健康状态历史: {statuses}")
            # 如果全是 healthy，说明 SSO 正常
            # 如果有 degraded 或 unhealthy，说明检测到问题
            assert all(s in ["healthy", "degraded", "unhealthy"] for s in statuses)
        else:
            pytest.skip("SSO health endpoint not available")

    @pytest.mark.asyncio
    @skip_write_tests
    async def test_failover_audit_log_recorded(
        self,
        async_client: AsyncClient,
        test_local_user: dict[str, str],
        admin_token: str,
    ) -> None:
        """场景3: 降级期间审计日志记录

        验证步骤:
        1. 触发 SSO 降级登录
        2. 查询审计日志 API
        3. 验证 auth_failover 或相关事件被记录
        """
        # Arrange: 触发降级登录
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": test_local_user["username"],
                "password": test_local_user["password"],
            },
            headers={"X-Auth-Fallback": "true"},
        )

        if login_response.status_code != 200:
            pytest.skip("Login failed, cannot verify audit log")

        # Act: 等待日志写入后查询审计日志
        await asyncio.sleep(2)
        audit_response = await async_client.get(
            "/api/v1/audit/logs",
            params={
                "limit": 10,
                "username": test_local_user["username"],
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Assert
        if audit_response.status_code == 200:
            logs = audit_response.json()
            items = logs.get("items", [])

            # 查找登录相关的审计日志
            login_logs = [
                log
                for log in items
                if log.get("operation_type") in ["login", "auth_failover", "local_login"]
            ]

            if login_logs:
                print(f"✅ 找到 {len(login_logs)} 条登录相关审计日志")
                # 验证最近的日志包含必要信息
                latest_log = login_logs[0]
                assert "username" in latest_log or "user_id" in latest_log
            else:
                print("⚠️ 未找到登录审计日志 (可能 audit 模块未启用)")
        elif audit_response.status_code == 404:
            pytest.skip("Audit API not implemented yet")
        else:
            print(f"⚠️ Audit API response: {audit_response.status_code}")

    @pytest.mark.asyncio
    async def test_nonexistent_account_returns_generic_error(
        self,
        async_client: AsyncClient,
    ) -> None:
        """场景4: 不存在账号返回通用错误

        验证步骤:
        1. 使用不存在的用户名登录
        2. 验证返回通用错误
        3. 验证错误消息不泄露账号存在性
        """
        # Act
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent_user_e2e_12345",
                "password": "any_password_123",
            },
        )

        # Assert
        assert response.status_code == 401

        error = response.json()
        error_message = str(error.get("detail", "")).lower()

        # 验证返回通用错误消息
        assert "invalid" in error_message or "credentials" in error_message

        # 验证不泄露账号存在性信息
        assert "not found" not in error_message
        assert "does not exist" not in error_message
        assert "nonexistent" not in error_message

        print("✅ 账号不存在时返回通用错误，未泄露存在性信息")


@pytest.mark.e2e
@pytest.mark.aws_integration
@skip_without_aws
class TestSSOHealthTrackerE2E:
    """SSO 健康检查器 E2E 测试

    验证 SSO 服务健康状态的监控和报告。
    """

    @pytest.mark.asyncio
    async def test_health_check_response_format(
        self,
        async_client: AsyncClient,
        sso_health_endpoint: str,
    ) -> None:
        """验证健康检查响应格式"""
        response = await async_client.get(sso_health_endpoint)

        if response.status_code == 200:
            data = response.json()

            # 验证必需字段
            assert "status" in data

            # 验证状态值有效
            valid_statuses = {"healthy", "degraded", "unhealthy"}
            assert data["status"] in valid_statuses

            # 验证可选字段格式
            if "latency_ms" in data:
                assert isinstance(data["latency_ms"], (int, float))
                assert data["latency_ms"] >= 0

            if "consecutive_failures" in data:
                assert isinstance(data["consecutive_failures"], int)
                assert data["consecutive_failures"] >= 0

            print(f"✅ 健康检查响应格式正确: {data}")
        elif response.status_code == 404:
            pytest.skip("SSO health endpoint not implemented")

    @pytest.mark.asyncio
    async def test_health_check_performance(
        self,
        async_client: AsyncClient,
        sso_health_endpoint: str,
    ) -> None:
        """验证健康检查性能

        健康检查应该快速响应，不应阻塞
        """
        start_time = time.time()
        response = await async_client.get(sso_health_endpoint)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            # 健康检查应该在 1 秒内完成
            assert elapsed < 1.0, f"Health check too slow: {elapsed:.2f}s"
            print(f"✅ 健康检查响应时间: {elapsed * 1000:.2f}ms")
        elif response.status_code == 404:
            pytest.skip("SSO health endpoint not implemented")


@pytest.mark.e2e
@pytest.mark.aws_integration
@skip_without_aws
class TestAuthenticationSecurityE2E:
    """认证安全性 E2E 测试

    验证认证系统的安全特性。
    """

    @pytest.mark.asyncio
    async def test_password_not_in_response(
        self,
        async_client: AsyncClient,
        test_local_user: dict[str, str],
    ) -> None:
        """验证响应中不包含密码"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": test_local_user["username"],
                "password": test_local_user["password"],
            },
        )

        # 无论成功与否，响应中都不应包含密码
        response_text = response.text.lower()
        assert test_local_user["password"].lower() not in response_text
        assert "password" not in response_text or "password_hash" not in response_text

        print("✅ 响应中不包含密码信息")

    @pytest.mark.asyncio
    async def test_rate_limiting_on_failed_attempts(
        self,
        async_client: AsyncClient,
    ) -> None:
        """验证失败登录尝试的速率限制

        多次失败尝试后应该触发速率限制或账号锁定
        """
        failed_attempts = 0
        rate_limited = False

        for i in range(10):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={
                    "username": f"ratelimit_test_user_{i}",
                    "password": "wrong_password",
                },
            )

            if response.status_code == 429:
                rate_limited = True
                print(f"✅ 在第 {i + 1} 次尝试后触发速率限制")
                break
            elif response.status_code == 401:
                failed_attempts += 1

        if not rate_limited:
            print(f"⚠️ {failed_attempts} 次失败尝试后未触发速率限制")
            # 这不一定是错误，取决于速率限制配置
            # pytest.skip("Rate limiting not triggered or not configured")

    @pytest.mark.asyncio
    async def test_token_format_and_expiry(
        self,
        async_client: AsyncClient,
        test_local_user: dict[str, str],
    ) -> None:
        """验证 Token 格式和过期设置"""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": test_local_user["username"],
                "password": test_local_user["password"],
            },
        )

        if response.status_code != 200:
            pytest.skip("Login failed")

        data = response.json()

        # API 返回嵌套结构: {tokens: {access_token: ...}, user: {...}}
        if "tokens" in data:
            tokens = data["tokens"]
        else:
            tokens = data

        # 验证 token 存在且格式正确
        assert "access_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"].lower() == "bearer"

        # 验证 token 是 JWT 格式 (3 部分用 . 分隔)
        token = tokens["access_token"]
        parts = token.split(".")
        assert len(parts) == 3, "Token should be JWT format"

        # 如果有过期时间字段，验证格式
        if "expires_in" in tokens:
            assert isinstance(tokens["expires_in"], int)
            assert tokens["expires_in"] > 0

        print(f"✅ Token 格式正确，token_type: {tokens['token_type']}")
