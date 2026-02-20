"""
Region 解析逻辑的单元测试.

测试 app.py 中 resolve_region / resolve_account 的优先级:
1. --context (显式 CLI 参数)
2. cdk.json defaultContext.environments.{env} (配置文件)
3. CDK_DEFAULT_REGION / CDK_DEFAULT_ACCOUNT (环境变量)
4. 兜底默认值 (us-east-1 / "")
"""

import json
import os
from unittest.mock import patch

import aws_cdk as cdk

from app import _resolve_from_cdk_json, resolve_account, resolve_region


class TestResolveFromCdkJson:
    """测试从 cdk.json 读取配置."""

    def test_reads_region_for_dev(self) -> None:
        """验证能正确读取 dev 环境的 region 配置."""
        result = _resolve_from_cdk_json("dev", "region")
        assert result == "us-east-1"

    def test_reads_region_for_prod(self) -> None:
        """验证能正确读取 prod 环境的 region 配置."""
        result = _resolve_from_cdk_json("prod", "region")
        assert result == "us-east-1"

    def test_returns_none_for_nonexistent_env(self) -> None:
        """验证不存在的环境名返回 None."""
        result = _resolve_from_cdk_json("nonexistent", "region")
        assert result is None

    def test_returns_none_for_empty_account(self) -> None:
        """验证空字符串 account 返回 None."""
        # cdk.json 中 dev 的 account 为空字符串
        result = _resolve_from_cdk_json("dev", "account")
        assert result is None

    def test_returns_none_for_missing_cdk_json(self) -> None:
        """验证 cdk.json 不存在时返回 None."""
        with patch("app.Path") as mock_path_cls:
            mock_path = mock_path_cls.return_value.__truediv__.return_value
            mock_path.exists.return_value = False
            result = _resolve_from_cdk_json("dev", "region")
            assert result is None

    def test_returns_none_for_invalid_json(self) -> None:
        """验证 cdk.json 格式错误时返回 None."""
        with patch("app.Path") as mock_path_cls:
            mock_path = mock_path_cls.return_value.__truediv__.return_value
            mock_path.exists.return_value = True

            # 模拟 open 读取损坏的文件
            with patch("builtins.open", side_effect=json.JSONDecodeError("", "", 0)):
                result = _resolve_from_cdk_json("dev", "region")
                assert result is None


class TestResolveRegion:
    """测试 region 解析优先级."""

    def test_default_region_without_env_vars(self) -> None:
        """无环境变量时默认 us-east-1."""
        app = cdk.App()
        env_vars = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CDK_DEFAULT_REGION", "AWS_REGION", "AWS_DEFAULT_REGION")
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # cdk.json 中 dev 的 region 就是 us-east-1，所以结果也是 us-east-1
            region = resolve_region(app, "dev")
            assert region == "us-east-1"

    def test_context_overrides_env_var(self) -> None:
        """--context region=xxx 优先于环境变量."""
        app = cdk.App(context={"region": "eu-west-1"})
        with patch.dict(os.environ, {"CDK_DEFAULT_REGION": "ap-southeast-1"}):
            region = resolve_region(app, "dev")
            assert region == "eu-west-1"

    def test_context_overrides_cdk_json(self) -> None:
        """--context region=xxx 优先于 cdk.json 配置."""
        app = cdk.App(context={"region": "ap-northeast-1"})
        region = resolve_region(app, "dev")
        # cdk.json dev.region = us-east-1，但 context 优先
        assert region == "ap-northeast-1"

    def test_cdk_json_overrides_env_var(self) -> None:
        """cdk.json 配置优先于 CDK_DEFAULT_REGION 环境变量."""
        app = cdk.App()
        with patch.dict(os.environ, {"CDK_DEFAULT_REGION": "us-west-2"}):
            region = resolve_region(app, "dev")
            # cdk.json dev.region = us-east-1，优先于环境变量 us-west-2
            assert region == "us-east-1"

    def test_env_var_used_when_cdk_json_missing_env(self) -> None:
        """cdk.json 中无对应环境时，回退到环境变量."""
        app = cdk.App()
        with patch.dict(os.environ, {"CDK_DEFAULT_REGION": "us-west-2"}):
            region = resolve_region(app, "nonexistent")
            assert region == "us-west-2"

    def test_fallback_to_default(self) -> None:
        """所有来源均无效时回退到 us-east-1."""
        app = cdk.App()
        env_vars = {
            k: v
            for k, v in os.environ.items()
            if k not in ("CDK_DEFAULT_REGION", "AWS_REGION", "AWS_DEFAULT_REGION")
        }
        with patch.dict(os.environ, env_vars, clear=True):
            region = resolve_region(app, "nonexistent")
            assert region == "us-east-1"


class TestResolveAccount:
    """测试 account 解析优先级."""

    def test_context_overrides_env_var(self) -> None:
        """--context account=xxx 优先于环境变量."""
        app = cdk.App(context={"account": "111111111111"})
        with patch.dict(os.environ, {"CDK_DEFAULT_ACCOUNT": "222222222222"}):
            account = resolve_account(app, "dev")
            assert account == "111111111111"

    def test_env_var_fallback(self) -> None:
        """无 context 和 cdk.json 配置时回退到环境变量."""
        app = cdk.App()
        with patch.dict(os.environ, {"CDK_DEFAULT_ACCOUNT": "333333333333"}):
            # cdk.json dev.account 为空字符串，视为无效
            account = resolve_account(app, "dev")
            assert account == "333333333333"

    def test_empty_string_fallback(self) -> None:
        """所有来源均无效时返回空字符串."""
        app = cdk.App()
        env_vars = {k: v for k, v in os.environ.items() if k != "CDK_DEFAULT_ACCOUNT"}
        with patch.dict(os.environ, env_vars, clear=True):
            account = resolve_account(app, "dev")
            assert account == ""
