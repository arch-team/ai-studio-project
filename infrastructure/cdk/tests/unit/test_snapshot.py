"""
Snapshot tests for CDK Stacks.

为每个 Stack 生成 CloudFormation 模板快照，防止意外变更。

首次运行时自动生成快照文件到 tests/unit/snapshots/ 目录。
后续运行会对比当前模板与快照，如有差异则测试失败。

有意变更: 使用 --snapshot-update 参数更新快照:
    pytest tests/unit/test_snapshot.py --snapshot-update
"""

import json
import re
from pathlib import Path

import aws_cdk as cdk
import pytest
from aws_cdk import aws_kms as kms
from aws_cdk.assertions import Template

from config import EnvironmentConfig
from stacks import (
    AlbStack,
    ApplicationStack,
    DatabaseStack,
    IamStack,
    NetworkStack,
    StorageStack,
)

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def _normalize_template(template: Template) -> dict:
    """移除模板中的动态值 (hash, 时间戳等) 以确保快照稳定性。

    保留完整资源结构（类型+属性），仅替换 CDK 生成的动态 hash/token。
    这样可以检测到资源属性变更，而非仅检测数量变化。
    """
    raw = template.to_json()
    # 保留完整结构，仅移除动态 hash 和 token
    normalized = json.dumps(raw, sort_keys=True)
    # 替换 64 位十六进制 hash (CDK asset hash)
    normalized = re.sub(r"[a-f0-9]{64}", "<HASH>", normalized)
    # 替换 8+ 位大写十六进制 token (CDK 逻辑 ID 后缀)
    normalized = re.sub(r"[A-F0-9]{8,}", "<TOKEN>", normalized)
    return json.loads(normalized)


def _save_snapshot(name: str, data: dict) -> None:
    """保存快照到文件。"""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = SNAPSHOT_DIR / f"{name}.json"
    snapshot_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _load_snapshot(name: str) -> dict | None:
    """加载快照文件，不存在则返回 None。"""
    snapshot_path = SNAPSHOT_DIR / f"{name}.json"
    if not snapshot_path.exists():
        return None
    return json.loads(snapshot_path.read_text())


def _assert_snapshot(name: str, template: Template, update: bool = False) -> None:
    """对比模板与快照。

    Args:
        name: 快照名称
        template: CloudFormation 模板
        update: 是否更新快照 (通过 --snapshot-update 标志)
    """
    current = _normalize_template(template)
    existing = _load_snapshot(name)

    if existing is None or update:
        _save_snapshot(name, current)
        if existing is None:
            pytest.skip(f"快照 {name} 首次生成，请重新运行测试")
        return

    assert current == existing, (
        f"Stack {name} 模板与快照不一致。\n"
        f"差异:\n"
        f"  当前 ResourceCount={current['ResourceCount']}, "
        f"快照 ResourceCount={existing['ResourceCount']}\n"
        f"  当前 OutputCount={current['OutputCount']}, "
        f"快照 OutputCount={existing['OutputCount']}\n"
        f"如果这是有意变更，请使用 --snapshot-update 更新快照。"
    )


@pytest.fixture
def snapshot_update(request: pytest.FixtureRequest) -> bool:
    """通过 SNAPSHOT_UPDATE 环境变量或 marker 控制快照更新."""
    import os

    return os.environ.get("SNAPSHOT_UPDATE", "0") == "1"


class TestNetworkStackSnapshot:
    """NetworkStack 快照测试."""

    def test_snapshot(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        snapshot_update: bool,
    ) -> None:
        stack = NetworkStack(
            cdk_app, "SnapshotNetwork", env_config=dev_config, env=cdk_env
        )
        _assert_snapshot("network_stack", Template.from_stack(stack), snapshot_update)


class TestIamStackSnapshot:
    """IamStack 快照测试."""

    def test_snapshot(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        snapshot_update: bool,
    ) -> None:
        stack = IamStack(cdk_app, "SnapshotIam", env_config=dev_config, env=cdk_env)
        _assert_snapshot("iam_stack", Template.from_stack(stack), snapshot_update)


class TestDatabaseStackSnapshot:
    """DatabaseStack 快照测试."""

    def test_snapshot(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        snapshot_update: bool,
    ) -> None:
        vpc_stack = NetworkStack(
            cdk_app, "SnapshotVpc", env_config=dev_config, env=cdk_env
        )
        stack = DatabaseStack(
            cdk_app,
            "SnapshotDatabase",
            env_config=dev_config,
            vpc=vpc_stack.vpc,
            env=cdk_env,
        )
        _assert_snapshot("database_stack", Template.from_stack(stack), snapshot_update)


class TestStorageStackSnapshot:
    """StorageStack 快照测试."""

    def test_snapshot(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        snapshot_update: bool,
        test_kms_key: kms.Key,
    ) -> None:
        stack = StorageStack(
            cdk_app,
            "SnapshotStorage",
            env_config=dev_config,
            encryption_key=test_kms_key,
            env=cdk_env,
        )
        _assert_snapshot("storage_stack", Template.from_stack(stack), snapshot_update)


class TestAlbStackSnapshot:
    """AlbStack 快照测试."""

    def test_snapshot(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        snapshot_update: bool,
    ) -> None:
        vpc_stack = NetworkStack(
            cdk_app, "SnapshotVpc", env_config=dev_config, env=cdk_env
        )
        stack = AlbStack(
            cdk_app,
            "SnapshotAlb",
            env_config=dev_config,
            vpc=vpc_stack.vpc,
            env=cdk_env,
        )
        _assert_snapshot("alb_stack", Template.from_stack(stack), snapshot_update)


class TestApplicationStackSnapshot:
    """ApplicationStack 快照测试."""

    def test_snapshot(
        self,
        cdk_app: cdk.App,
        dev_config: EnvironmentConfig,
        cdk_env: cdk.Environment,
        snapshot_update: bool,
    ) -> None:
        stack = ApplicationStack(
            cdk_app, "SnapshotApplication", env_config=dev_config, env=cdk_env
        )
        _assert_snapshot(
            "application_stack", Template.from_stack(stack), snapshot_update
        )
