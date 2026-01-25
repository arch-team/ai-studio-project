"""测试上传状态值对象 (UploadPart, UploadSession)。"""

from datetime import datetime
from enum import Enum

import pytest


class TestUploadStatus:
    """测试 UploadStatus 枚举。"""

    def test_upload_status_values(self) -> None:
        """验证上传状态枚举值。"""
        from src.modules.datasets.domain.value_objects import UploadStatus

        assert UploadStatus.INITIATED.value == "INITIATED"
        assert UploadStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert UploadStatus.COMPLETING.value == "COMPLETING"
        assert UploadStatus.COMPLETED.value == "COMPLETED"
        assert UploadStatus.ABORTED.value == "ABORTED"
        assert UploadStatus.FAILED.value == "FAILED"

    def test_upload_status_is_enum(self) -> None:
        """验证是 Enum 类型。"""
        from src.modules.datasets.domain.value_objects import UploadStatus

        assert issubclass(UploadStatus, Enum)

    def test_upload_status_count(self) -> None:
        """验证枚举值数量。"""
        from src.modules.datasets.domain.value_objects import UploadStatus

        assert len(UploadStatus) == 6


class TestUploadPart:
    """测试 UploadPart 值对象。"""

    def test_create_upload_part(self) -> None:
        """创建有效的 UploadPart。"""
        from src.modules.datasets.domain.value_objects import UploadPart

        now = datetime.now()
        part = UploadPart(
            part_number=1,
            etag='"abc123"',
            size_bytes=100_000_000,
            md5_checksum="d41d8cd98f00b204e9800998ecf8427e",
            uploaded_at=now,
        )

        assert part.part_number == 1
        assert part.etag == '"abc123"'
        assert part.size_bytes == 100_000_000
        assert part.md5_checksum == "d41d8cd98f00b204e9800998ecf8427e"
        assert part.uploaded_at == now

    def test_upload_part_is_frozen(self) -> None:
        """验证 UploadPart 不可变。"""
        from src.modules.datasets.domain.value_objects import UploadPart

        part = UploadPart(
            part_number=1,
            etag='"abc123"',
            size_bytes=100_000_000,
            md5_checksum="d41d8cd98f00b204e9800998ecf8427e",
            uploaded_at=datetime.now(),
        )

        with pytest.raises(AttributeError):
            part.part_number = 2  # type: ignore

    def test_upload_part_invalid_part_number_zero(self) -> None:
        """part_number 为 0 应该失败。"""
        from src.modules.datasets.domain.value_objects import UploadPart

        with pytest.raises(ValueError, match="part_number"):
            UploadPart(
                part_number=0,
                etag='"abc"',
                size_bytes=100,
                md5_checksum="xxx",
                uploaded_at=datetime.now(),
            )

    def test_upload_part_invalid_part_number_too_large(self) -> None:
        """part_number 超过 10000 应该失败。"""
        from src.modules.datasets.domain.value_objects import UploadPart

        with pytest.raises(ValueError, match="part_number"):
            UploadPart(
                part_number=10001,
                etag='"abc"',
                size_bytes=100,
                md5_checksum="xxx",
                uploaded_at=datetime.now(),
            )

    def test_upload_part_invalid_negative_size(self) -> None:
        """size_bytes 为负数应该失败。"""
        from src.modules.datasets.domain.value_objects import UploadPart

        with pytest.raises(ValueError, match="size_bytes"):
            UploadPart(
                part_number=1,
                etag='"abc"',
                size_bytes=-1,
                md5_checksum="xxx",
                uploaded_at=datetime.now(),
            )

    def test_upload_part_max_valid_part_number(self) -> None:
        """part_number 为 10000 应该成功。"""
        from src.modules.datasets.domain.value_objects import UploadPart

        part = UploadPart(
            part_number=10000,
            etag='"abc"',
            size_bytes=100,
            md5_checksum="xxx",
            uploaded_at=datetime.now(),
        )
        assert part.part_number == 10000

    def test_upload_part_equality(self) -> None:
        """相同值的 UploadPart 应该相等。"""
        from src.modules.datasets.domain.value_objects import UploadPart

        now = datetime.now()
        part1 = UploadPart(
            part_number=1,
            etag='"abc"',
            size_bytes=100,
            md5_checksum="xxx",
            uploaded_at=now,
        )
        part2 = UploadPart(
            part_number=1,
            etag='"abc"',
            size_bytes=100,
            md5_checksum="xxx",
            uploaded_at=now,
        )
        assert part1 == part2


class TestUploadSession:
    """测试 UploadSession 领域对象。"""

    def test_create_upload_session(self) -> None:
        """创建有效的 UploadSession。"""
        from src.modules.datasets.domain.value_objects import (
            UploadSession,
            UploadStatus,
        )

        session = UploadSession(
            upload_id="abc123",
            dataset_id=1,
            bucket="my-bucket",
            key="datasets/1/data.tar",
            filename="data.tar",
            content_type="application/x-tar",
            total_size=500_000_000,  # 500 MB
            part_size=100_000_000,  # 100 MB
            status=UploadStatus.INITIATED,
            owner_id=100,
        )

        assert session.upload_id == "abc123"
        assert session.dataset_id == 1
        assert session.total_size == 500_000_000
        assert session.status == UploadStatus.INITIATED

    def test_expected_part_count(self) -> None:
        """验证预期分片数计算。"""
        from src.modules.datasets.domain.value_objects import (
            UploadSession,
            UploadStatus,
        )

        # 500MB 文件，100MB 分片 → 5 个分片
        session = UploadSession(
            upload_id="abc",
            dataset_id=1,
            bucket="bucket",
            key="key",
            filename="file",
            content_type="application/octet-stream",
            total_size=500_000_000,
            part_size=100_000_000,
            status=UploadStatus.INITIATED,
            owner_id=1,
        )
        assert session.expected_part_count == 5

        # 501MB 文件，100MB 分片 → 6 个分片 (向上取整)
        session2 = UploadSession(
            upload_id="abc2",
            dataset_id=1,
            bucket="bucket",
            key="key",
            filename="file",
            content_type="application/octet-stream",
            total_size=501_000_000,
            part_size=100_000_000,
            status=UploadStatus.INITIATED,
            owner_id=1,
        )
        assert session2.expected_part_count == 6

    def test_uploaded_bytes(self) -> None:
        """验证已上传字节数计算。"""
        from src.modules.datasets.domain.value_objects import (
            UploadPart,
            UploadSession,
            UploadStatus,
        )

        session = UploadSession(
            upload_id="abc",
            dataset_id=1,
            bucket="bucket",
            key="key",
            filename="file",
            content_type="application/octet-stream",
            total_size=500_000_000,
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=1,
        )

        # 初始为 0
        assert session.uploaded_bytes == 0

        # 添加两个分片
        now = datetime.now()
        part1 = UploadPart(
            part_number=1,
            etag='"etag1"',
            size_bytes=100_000_000,
            md5_checksum="md51",
            uploaded_at=now,
        )
        part2 = UploadPart(
            part_number=2,
            etag='"etag2"',
            size_bytes=100_000_000,
            md5_checksum="md52",
            uploaded_at=now,
        )
        session.add_part(part1)
        session.add_part(part2)

        assert session.uploaded_bytes == 200_000_000

    def test_progress_percentage(self) -> None:
        """验证进度百分比计算。"""
        from src.modules.datasets.domain.value_objects import (
            UploadPart,
            UploadSession,
            UploadStatus,
        )

        session = UploadSession(
            upload_id="abc",
            dataset_id=1,
            bucket="bucket",
            key="key",
            filename="file",
            content_type="application/octet-stream",
            total_size=500_000_000,
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=1,
        )

        # 初始为 0%
        assert session.progress_percentage == 0.0

        # 添加 2/5 分片 → 40%
        now = datetime.now()
        session.add_part(UploadPart(1, '"e1"', 100_000_000, "m1", now))
        session.add_part(UploadPart(2, '"e2"', 100_000_000, "m2", now))

        assert session.progress_percentage == 40.0

    def test_missing_parts(self) -> None:
        """验证缺失分片计算（断点续传关键）。"""
        from src.modules.datasets.domain.value_objects import (
            UploadPart,
            UploadSession,
            UploadStatus,
        )

        session = UploadSession(
            upload_id="abc",
            dataset_id=1,
            bucket="bucket",
            key="key",
            filename="file",
            content_type="application/octet-stream",
            total_size=500_000_000,  # 5 个分片
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=1,
        )

        # 初始缺失 [1,2,3,4,5]
        assert session.missing_parts == [1, 2, 3, 4, 5]

        # 完成分片 1 和 3
        now = datetime.now()
        session.add_part(UploadPart(1, '"e1"', 100_000_000, "m1", now))
        session.add_part(UploadPart(3, '"e3"', 100_000_000, "m3", now))

        # 缺失 [2, 4, 5]
        assert session.missing_parts == [2, 4, 5]

    def test_is_complete(self) -> None:
        """验证完成状态检查。"""
        from src.modules.datasets.domain.value_objects import (
            UploadPart,
            UploadSession,
            UploadStatus,
        )

        session = UploadSession(
            upload_id="abc",
            dataset_id=1,
            bucket="bucket",
            key="key",
            filename="file",
            content_type="application/octet-stream",
            total_size=200_000_000,  # 2 个分片
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=1,
        )

        assert session.is_complete() is False

        now = datetime.now()
        session.add_part(UploadPart(1, '"e1"', 100_000_000, "m1", now))
        assert session.is_complete() is False

        session.add_part(UploadPart(2, '"e2"', 100_000_000, "m2", now))
        assert session.is_complete() is True

    def test_add_part_updates_timestamp(self) -> None:
        """验证 add_part 更新时间戳。"""
        from src.modules.datasets.domain.value_objects import (
            UploadPart,
            UploadSession,
            UploadStatus,
        )

        session = UploadSession(
            upload_id="abc",
            dataset_id=1,
            bucket="bucket",
            key="key",
            filename="file",
            content_type="application/octet-stream",
            total_size=200_000_000,
            part_size=100_000_000,
            status=UploadStatus.IN_PROGRESS,
            owner_id=1,
        )

        original_updated = session.updated_at

        # 添加分片
        import time

        time.sleep(0.01)  # 确保时间差异
        session.add_part(UploadPart(1, '"e1"', 100_000_000, "m1", datetime.now()))

        assert session.updated_at > original_updated

    def test_zero_size_file_progress(self) -> None:
        """验证零字节文件的进度计算。"""
        from src.modules.datasets.domain.value_objects import (
            UploadSession,
            UploadStatus,
        )

        session = UploadSession(
            upload_id="abc",
            dataset_id=1,
            bucket="bucket",
            key="key",
            filename="empty.txt",
            content_type="text/plain",
            total_size=0,
            part_size=100_000_000,
            status=UploadStatus.INITIATED,
            owner_id=1,
        )

        # 零字节文件进度应该是 100%
        assert session.progress_percentage == 100.0
