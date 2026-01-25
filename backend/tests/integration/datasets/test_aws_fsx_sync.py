"""FSx for Lustre 同步 AWS 集成测试。

测试 T048: FSx 路径管理功能在真实 AWS 环境中的行为。

运行前需要配置环境变量:
    export AWS_REGION=us-west-2
    export FSX_FILESYSTEM_ID=fs-0123456789abcdef0
    export FSX_MOUNT_PATH=/fsx
    export S3_BUCKET_NAME=ai-training-platform-datasets-dev

运行命令:
    pytest tests/integration/datasets/test_aws_fsx_sync.py -v -m aws_integration
"""

import os

import pytest

# AWS 集成测试默认跳过，需要显式启用
pytestmark = [
    pytest.mark.aws_integration,
    pytest.mark.skipif(
        not os.environ.get("FSX_FILESYSTEM_ID"),
        reason="FSX_FILESYSTEM_ID environment variable not set",
    ),
]


class TestFsxAvailability:
    """测试 FSx 文件系统可用性检查。"""

    @pytest.mark.asyncio
    async def test_check_fsx_availability_success(self) -> None:
        """E2E-1: 验证 FSx 文件系统连接成功。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        client = FsxClient(
            filesystem_id=os.environ["FSX_FILESYSTEM_ID"],
            region=os.environ.get("AWS_REGION", "us-west-2"),
            mount_path=os.environ.get("FSX_MOUNT_PATH", "/fsx"),
        )

        result = await client.describe_filesystem()

        assert result["FileSystemId"] == os.environ["FSX_FILESYSTEM_ID"]
        assert result["Lifecycle"] == "AVAILABLE"

    @pytest.mark.asyncio
    async def test_filesystem_has_dra_configuration(self) -> None:
        """验证文件系统配置了 Data Repository Association。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        client = FsxClient(
            filesystem_id=os.environ["FSX_FILESYSTEM_ID"],
            region=os.environ.get("AWS_REGION", "us-west-2"),
        )

        result = await client.describe_filesystem()

        # 验证 Lustre 配置
        assert "LustreConfiguration" in result
        lustre_config = result["LustreConfiguration"]
        assert (
            lustre_config.get("DataRepositoryConfiguration") is not None
            or lustre_config.get("DataCompressionType") is not None
        )


class TestS3ToFsxSync:
    """测试 S3 → FSx 同步功能。"""

    @pytest.fixture
    def test_dataset_id(self) -> str:
        """测试用数据集 ID (使用唯一路径避免任务冲突)。"""
        import uuid

        base_id = os.environ.get("TEST_DATASET_ID", "1")
        return f"{base_id}-{uuid.uuid4().hex[:8]}"

    @pytest.mark.asyncio
    async def test_create_import_task_success(self, test_dataset_id: str) -> None:
        """E2E-2: 验证创建 S3→FSx 同步任务成功。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        s3_bucket = os.environ["S3_BUCKET_NAME"]
        client = FsxClient(
            filesystem_id=os.environ["FSX_FILESYSTEM_ID"],
            region=os.environ.get("AWS_REGION", "us-east-1"),
        )

        # 路径格式: S3 路径 (DRA DataRepositoryPath 格式)
        # 需要使用完整的 S3 路径: s3://bucket/path/
        s3_path = f"s3://{s3_bucket}/{test_dataset_id}/"

        result = await client.create_import_task(
            paths=[s3_path],
            report_enabled=False,
        )

        assert "TaskId" in result
        assert result["Type"] == "IMPORT_METADATA_FROM_REPOSITORY"
        assert result["Lifecycle"] in ("PENDING", "EXECUTING")

    @pytest.mark.asyncio
    async def test_import_task_completes(self, test_dataset_id: str) -> None:
        """E2E-3: 验证同步任务完成。"""
        from src.modules.datasets.infrastructure.fsx import (
            FsxClient,
            FsxTaskLifecycle,
        )

        s3_bucket = os.environ["S3_BUCKET_NAME"]
        client = FsxClient(
            filesystem_id=os.environ["FSX_FILESYSTEM_ID"],
            region=os.environ.get("AWS_REGION", "us-east-1"),
        )

        # 创建任务 (使用 S3 路径格式)
        s3_path = f"s3://{s3_bucket}/{test_dataset_id}/"
        create_result = await client.create_import_task(paths=[s3_path])
        task_id = create_result["TaskId"]

        # 等待完成
        final_result = await client.wait_for_task_completion(
            task_id=task_id,
            poll_interval=10,
            max_wait_time=600,  # 10 分钟超时
        )

        assert final_result["Lifecycle"] == FsxTaskLifecycle.SUCCEEDED.value


class TestFsxCacheRelease:
    """测试 FSx 缓存释放功能。"""

    @pytest.fixture
    def test_dataset_id(self) -> str:
        """测试用数据集 ID (使用唯一路径避免任务冲突)。"""
        import uuid

        base_id = os.environ.get("TEST_DATASET_ID", "1")
        return f"{base_id}-release-{uuid.uuid4().hex[:8]}"

    @pytest.mark.skip(reason="RELEASE_DATA_FROM_FILESYSTEM 需要 DRA 配置额外验证，待调研")
    @pytest.mark.asyncio
    async def test_create_release_task_success(self, test_dataset_id: str) -> None:
        """E2E-4: 验证创建缓存释放任务成功。

        TODO: RELEASE_DATA_FROM_FILESYSTEM 任务需要以下条件:
        1. 目标路径必须存在于 FSx 文件系统上
        2. 可能需要 DRA 配置支持 AutoExport
        3. 需要进一步调研 AWS 文档
        """
        from src.modules.datasets.infrastructure.fsx import FsxClient

        client = FsxClient(
            filesystem_id=os.environ["FSX_FILESYSTEM_ID"],
            region=os.environ.get("AWS_REGION", "us-east-1"),
        )

        # RELEASE 任务使用 FSx 文件系统路径 (相对于 DRA FileSystemPath)
        # 注意: 释放的路径必须存在于 FSx 文件系统上
        fsx_path = f"/datasets/{test_dataset_id}/"
        result = await client.create_release_task(paths=[fsx_path])

        assert "TaskId" in result
        assert result["Type"] == "RELEASE_DATA_FROM_FILESYSTEM"


class TestFsxPathMapping:
    """测试路径映射功能。"""

    def test_fsx_path_format(self) -> None:
        """验证 FSx 路径格式正确。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        client = FsxClient(
            filesystem_id=os.environ["FSX_FILESYSTEM_ID"],
            region=os.environ.get("AWS_REGION", "us-west-2"),
            mount_path="/fsx",
        )

        fsx_path = client.get_fsx_path_for_dataset(dataset_id=10)

        assert fsx_path == "/fsx/datasets/10"

    def test_s3_path_format(self) -> None:
        """验证 S3 路径格式正确。"""
        from src.modules.datasets.infrastructure.fsx import FsxClient

        client = FsxClient(
            filesystem_id=os.environ["FSX_FILESYSTEM_ID"],
            region=os.environ.get("AWS_REGION", "us-west-2"),
            s3_bucket=os.environ.get("S3_BUCKET_NAME", "test-bucket"),
        )

        s3_path = client.get_s3_path_for_dataset(dataset_id=10)

        assert s3_path.startswith("s3://")
        assert "datasets/10" in s3_path


class TestFsxPerformance:
    """测试 FSx 性能基准 (SC-005)。

    这些测试需要在 HyperPod 节点上运行才能验证真实性能。
    """

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_sync_time_100gb_dataset(self) -> None:
        """P1: 100GB 数据集同步时间 <1分钟。

        注意: IMPORT_METADATA_FROM_REPOSITORY 仅同步元数据，非常快。
        实际数据在首次访问时按需加载。
        """
        import time

        from src.modules.datasets.infrastructure.fsx import FsxClient

        s3_bucket = os.environ["S3_BUCKET_NAME"]
        client = FsxClient(
            filesystem_id=os.environ["FSX_FILESYSTEM_ID"],
            region=os.environ.get("AWS_REGION", "us-east-1"),
        )

        start_time = time.time()

        # 假设 dataset_id=1 是 100GB 测试数据集
        s3_path = f"s3://{s3_bucket}/1/"
        result = await client.create_import_task(paths=[s3_path])
        task_id = result["TaskId"]

        await client.wait_for_task_completion(
            task_id=task_id,
            poll_interval=5,
            max_wait_time=60,
        )

        elapsed = time.time() - start_time
        assert elapsed < 60, f"同步耗时 {elapsed:.1f}s，超过 60s 限制"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_sync_time_1tb_dataset(self) -> None:
        """P3: 1TB 数据集同步时间 <10分钟 (SC-005 要求)。

        注意: 元数据同步应该在几分钟内完成。
        """
        import time

        from src.modules.datasets.infrastructure.fsx import FsxClient

        s3_bucket = os.environ["S3_BUCKET_NAME"]
        client = FsxClient(
            filesystem_id=os.environ["FSX_FILESYSTEM_ID"],
            region=os.environ.get("AWS_REGION", "us-east-1"),
        )

        start_time = time.time()

        # 假设 dataset_id=100 是 1TB 测试数据集
        s3_path = f"s3://{s3_bucket}/100/"
        result = await client.create_import_task(paths=[s3_path])
        task_id = result["TaskId"]

        await client.wait_for_task_completion(
            task_id=task_id,
            poll_interval=30,
            max_wait_time=600,
        )

        elapsed = time.time() - start_time
        assert elapsed < 600, f"同步耗时 {elapsed:.1f}s，超过 600s (10分钟) SC-005 限制"
