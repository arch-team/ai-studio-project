"""上传状态值对象 - S3 分片上传状态追踪。"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.shared.utils import utc_now


class UploadStatus(Enum):
    """上传会话状态枚举。"""

    INITIATED = "INITIATED"  # 已初始化，等待上传
    IN_PROGRESS = "IN_PROGRESS"  # 上传进行中
    COMPLETING = "COMPLETING"  # 正在完成合并
    COMPLETED = "COMPLETED"  # 上传完成
    ABORTED = "ABORTED"  # 已取消
    FAILED = "FAILED"  # 上传失败


@dataclass(frozen=True)
class UploadPart:
    """上传分片值对象 - 不可变，代表已完成的一个分片。

    Attributes:
        part_number: 分片编号 (1-10000，S3 限制)
        etag: S3 返回的 ETag
        size_bytes: 分片大小 (字节)
        md5_checksum: MD5 校验和
        uploaded_at: 上传完成时间
    """

    part_number: int
    etag: str
    size_bytes: int
    md5_checksum: str
    uploaded_at: datetime

    def __post_init__(self) -> None:
        """验证分片参数有效性。"""
        # S3 分片编号范围: 1-10000
        if self.part_number < 1 or self.part_number > 10000:
            raise ValueError(f"part_number must be between 1 and 10000, got {self.part_number}")
        # 分片大小不能为负
        if self.size_bytes < 0:
            raise ValueError(f"size_bytes must be non-negative, got {self.size_bytes}")


@dataclass
class UploadSession:
    """上传会话领域对象 - 追踪分片上传进度，支持断点续传。

    Attributes:
        upload_id: S3 Multipart Upload ID
        dataset_id: 关联数据集 ID
        bucket: S3 桶名
        key: S3 对象键
        filename: 原始文件名
        content_type: MIME 类型
        total_size: 文件总大小 (字节)
        part_size: 分片大小 (字节)
        status: 上传状态
        owner_id: 上传者用户 ID
        completed_parts: 已完成分片字典 {part_number: UploadPart}
        created_at: 创建时间
        updated_at: 更新时间
    """

    upload_id: str
    dataset_id: int
    bucket: str
    key: str
    filename: str
    content_type: str
    total_size: int
    part_size: int
    status: UploadStatus
    owner_id: int
    completed_parts: dict[int, UploadPart] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    @property
    def expected_part_count(self) -> int:
        """计算预期分片数 (向上取整)。"""
        if self.total_size == 0:
            return 0
        return (self.total_size + self.part_size - 1) // self.part_size

    @property
    def uploaded_bytes(self) -> int:
        """计算已上传字节数。"""
        return sum(part.size_bytes for part in self.completed_parts.values())

    @property
    def progress_percentage(self) -> float:
        """计算上传进度百分比。"""
        if self.total_size == 0:
            return 100.0  # 零字节文件视为 100%
        return (self.uploaded_bytes / self.total_size) * 100

    @property
    def missing_parts(self) -> list[int]:
        """获取缺失的分片编号列表 (断点续传关键)。"""
        expected = set(range(1, self.expected_part_count + 1))
        completed = set(self.completed_parts.keys())
        return sorted(expected - completed)

    def is_complete(self) -> bool:
        """检查所有分片是否已上传完成。"""
        return len(self.missing_parts) == 0

    def add_part(self, part: UploadPart) -> None:
        """添加已完成的分片。

        Args:
            part: 已完成的分片

        Note:
            此方法会更新 updated_at 时间戳
        """
        self.completed_parts[part.part_number] = part
        self.updated_at = utc_now()
