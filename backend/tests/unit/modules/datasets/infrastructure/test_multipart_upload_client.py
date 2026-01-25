"""测试 S3 Multipart Upload Client。"""

import pytest


class TestCalculateOptimalPartSize:
    """测试 calculate_optimal_part_size 函数。"""

    def test_small_file_uses_default_part_size(self) -> None:
        """验证小文件 (≤1TB) 使用默认 100MB 分片。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            DEFAULT_PART_SIZE,
            calculate_optimal_part_size,
        )

        # 100GB 文件
        file_size = 100 * 1024 * 1024 * 1024
        assert calculate_optimal_part_size(file_size) == DEFAULT_PART_SIZE

    def test_1tb_file_uses_default_part_size(self) -> None:
        """验证 1TB 文件使用默认 100MB 分片。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            DEFAULT_PART_SIZE,
            MAX_PARTS,
            calculate_optimal_part_size,
        )

        # 正好 1TB (100MB * 10000)
        file_size = DEFAULT_PART_SIZE * MAX_PARTS
        assert calculate_optimal_part_size(file_size) == DEFAULT_PART_SIZE

    def test_2tb_file_increases_part_size(self) -> None:
        """验证 2TB 文件增大分片大小。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            DEFAULT_PART_SIZE,
            MAX_PARTS,
            calculate_optimal_part_size,
        )

        # 2TB 文件
        file_size = 2 * 1024 * 1024 * 1024 * 1024
        part_size = calculate_optimal_part_size(file_size)

        # 分片大小应该大于默认值
        assert part_size > DEFAULT_PART_SIZE
        # 应该确保分片数量不超过 10000
        assert file_size / part_size <= MAX_PARTS

    def test_5tb_file_max_allowed(self) -> None:
        """验证 5TB 文件（S3 最大限制）可以计算分片大小。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            MAX_PARTS,
            MAX_SINGLE_FILE_SIZE,
            calculate_optimal_part_size,
        )

        # 正好 5TB
        file_size = MAX_SINGLE_FILE_SIZE
        part_size = calculate_optimal_part_size(file_size)

        # 应该确保分片数量不超过 10000
        assert file_size / part_size <= MAX_PARTS

    def test_exceeds_5tb_raises_error(self) -> None:
        """验证超过 5TB 限制抛出异常。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            MAX_SINGLE_FILE_SIZE,
            calculate_optimal_part_size,
        )

        # 超过 5TB
        file_size = MAX_SINGLE_FILE_SIZE + 1

        with pytest.raises(ValueError, match="exceeds S3 maximum"):
            calculate_optimal_part_size(file_size)

    def test_part_size_aligned_to_1mb(self) -> None:
        """验证分片大小对齐到 1MB 边界。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            DEFAULT_PART_SIZE,
            MAX_PARTS,
            calculate_optimal_part_size,
        )

        # 略大于 1TB 的文件
        file_size = DEFAULT_PART_SIZE * MAX_PARTS + 1024 * 1024
        part_size = calculate_optimal_part_size(file_size)

        # 验证对齐到 1MB 边界
        assert part_size % (1024 * 1024) == 0


class TestS3MultipartConstants:
    """测试 S3 分片上传常量。"""

    def test_default_part_size_is_100mb(self) -> None:
        """验证默认分片大小为 100MB。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            DEFAULT_PART_SIZE,
        )

        assert DEFAULT_PART_SIZE == 100 * 1024 * 1024

    def test_min_part_size_is_5mb(self) -> None:
        """验证最小分片大小为 5MB (S3 限制)。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            MIN_PART_SIZE,
        )

        assert MIN_PART_SIZE == 5 * 1024 * 1024

    def test_max_part_size_is_5gb(self) -> None:
        """验证最大分片大小为 5GB (S3 限制)。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            MAX_PART_SIZE,
        )

        assert MAX_PART_SIZE == 5 * 1024 * 1024 * 1024

    def test_max_parts_is_10000(self) -> None:
        """验证最大分片数为 10000 (S3 限制)。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            MAX_PARTS,
        )

        assert MAX_PARTS == 10000

    def test_max_single_file_size_is_5tb(self) -> None:
        """验证单文件最大为 5TB (S3 限制)。"""
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            MAX_SINGLE_FILE_SIZE,
        )

        assert MAX_SINGLE_FILE_SIZE == 5 * 1024 * 1024 * 1024 * 1024

    def test_fr007_large_dataset_support(self) -> None:
        """验证 FR-007: 支持 ≥10TB 数据集（多文件）。

        单文件最大 5TB，10TB 数据集需要 2+ 文件。
        每个文件可以用 calculate_optimal_part_size 计算分片。
        """
        from src.modules.datasets.infrastructure.s3.multipart_upload_client import (
            MAX_PARTS,
            MAX_SINGLE_FILE_SIZE,
            calculate_optimal_part_size,
        )

        # 验证 5TB 单文件可以正常处理
        part_size = calculate_optimal_part_size(MAX_SINGLE_FILE_SIZE)
        parts_needed = (MAX_SINGLE_FILE_SIZE + part_size - 1) // part_size

        assert parts_needed <= MAX_PARTS
        assert MAX_SINGLE_FILE_SIZE * 2 >= 10 * 1024 * 1024 * 1024 * 1024  # 2 files >= 10TB
