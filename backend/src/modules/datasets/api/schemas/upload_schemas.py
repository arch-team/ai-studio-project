"""Dataset Upload API schemas - 分片上传请求/响应模型。"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class UploadStatusEnum(str, Enum):
    """上传状态枚举 (API 层)。"""

    INITIATED = "INITIATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETING = "COMPLETING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    FAILED = "FAILED"


# ========== 请求 Schema ==========


class InitiateUploadRequest(BaseModel):
    """初始化分片上传请求。"""

    filename: str = Field(..., min_length=1, max_length=256, description="原始文件名")
    content_type: str = Field(
        default="application/octet-stream",
        max_length=128,
        description="MIME 类型",
    )
    total_size: int = Field(..., gt=0, description="文件总大小 (字节)")
    part_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        gt=5 * 1024 * 1024,  # 最小 5MB
        description="分片大小 (字节)",
    )


class GeneratePresignedUrlsRequest(BaseModel):
    """生成预签名 URL 请求。"""

    part_numbers: list[int] = Field(
        ...,
        min_length=1,
        description="需要上传的分片编号列表",
    )
    expiration: int = Field(
        default=3600,
        gt=0,
        le=86400,  # 最大 24 小时
        description="URL 过期时间 (秒)",
    )


class RegisterPartRequest(BaseModel):
    """注册分片完成请求。"""

    part_number: int = Field(..., ge=1, le=10000, description="分片编号")
    etag: str = Field(..., min_length=1, description="S3 返回的 ETag")
    size_bytes: int = Field(..., gt=0, description="分片大小 (字节)")
    md5_checksum: str = Field(default="", description="MD5 校验和")


# ========== 响应 Schema ==========


class InitiateUploadResponse(BaseModel):
    """初始化分片上传响应。"""

    upload_id: str = Field(..., description="S3 Multipart Upload ID")
    dataset_id: int = Field(..., description="数据集 ID")
    bucket: str = Field(..., description="S3 桶名")
    key: str = Field(..., description="S3 对象键")
    expected_part_count: int = Field(..., description="预期分片数")
    part_size: int = Field(..., description="分片大小 (字节)")


class PresignedUrlItem(BaseModel):
    """预签名 URL 项。"""

    part_number: int = Field(..., description="分片编号")
    presigned_url: str = Field(..., description="预签名 URL")


class PresignedUrlsResponse(BaseModel):
    """预签名 URL 响应。"""

    upload_id: str = Field(..., description="上传会话 ID")
    urls: list[PresignedUrlItem] = Field(..., description="预签名 URL 列表")
    expiration: int = Field(..., description="URL 过期时间 (秒)")


class UploadProgressResponse(BaseModel):
    """上传进度响应。"""

    upload_id: str = Field(..., description="上传会话 ID")
    dataset_id: int = Field(..., description="数据集 ID")
    filename: str = Field(..., description="文件名")
    total_size: int = Field(..., description="文件总大小 (字节)")
    uploaded_bytes: int = Field(..., description="已上传字节数")
    progress_percentage: float = Field(..., description="上传进度百分比")
    expected_part_count: int = Field(..., description="预期分片数")
    completed_part_count: int = Field(..., description="已完成分片数")
    missing_parts: list[int] = Field(..., description="缺失的分片编号列表")
    status: UploadStatusEnum = Field(..., description="上传状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class CompleteUploadResponse(BaseModel):
    """完成上传响应。"""

    etag: str = Field(..., description="S3 对象 ETag")
    location: str | None = Field(None, description="S3 对象 URL")
    bucket: str = Field(..., description="S3 桶名")
    key: str = Field(..., description="S3 对象键")
    size: int = Field(..., description="文件大小 (字节)")
