"""UploadSession 仓库实现 - SQLAlchemy 数据访问。"""

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.datasets.domain.repositories import IUploadSessionRepository
from src.modules.datasets.domain.value_objects import (
    UploadPart,
    UploadSession,
    UploadStatus,
)
from src.modules.datasets.infrastructure.models import (
    UploadSessionModel,
    UploadSessionStatus,
)
from src.shared.infrastructure.base_repository import BaseRepository


class UploadSessionRepositoryImpl(
    BaseRepository[UploadSession, UploadSessionModel, int],
    IUploadSessionRepository,
):
    """UploadSession 仓库 SQLAlchemy 实现。"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UploadSessionModel)

    def _domain_status_to_model(self, status: UploadStatus) -> UploadSessionStatus:
        """领域状态转换为 ORM 枚举。"""
        return UploadSessionStatus(status.value)

    def _model_status_to_domain(self, status: UploadSessionStatus) -> UploadStatus:
        """ORM 枚举转换为领域状态。"""
        return UploadStatus(status.value)

    def _to_entity(self, model: UploadSessionModel) -> UploadSession:
        """ORM 模型转换为领域对象。"""
        # 解析已完成分片 (JSON → dict[int, UploadPart])
        completed_parts: dict[int, UploadPart] = {}
        if model.completed_parts:
            for part_data in model.completed_parts:
                part_number = part_data["part_number"]
                uploaded_at = part_data.get("uploaded_at")
                if isinstance(uploaded_at, str):
                    uploaded_at = datetime.fromisoformat(uploaded_at)
                elif uploaded_at is None:
                    uploaded_at = model.updated_at

                completed_parts[part_number] = UploadPart(
                    part_number=part_number,
                    etag=part_data["etag"],
                    size_bytes=part_data["size_bytes"],
                    md5_checksum=part_data.get("md5_checksum", ""),
                    uploaded_at=uploaded_at,
                )

        return UploadSession(
            upload_id=model.upload_id,
            dataset_id=model.dataset_id,
            bucket=model.bucket,
            key=model.s3_key,
            filename=model.filename,
            content_type=model.content_type,
            total_size=model.total_size,
            part_size=model.part_size,
            status=self._model_status_to_domain(model.status),
            owner_id=model.owner_id,
            completed_parts=completed_parts,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: UploadSession) -> UploadSessionModel:
        """领域对象转换为 ORM 模型。"""
        # 序列化已完成分片 (dict[int, UploadPart] → JSON)
        completed_parts_json = None
        if entity.completed_parts:
            completed_parts_json = [
                {
                    "part_number": part.part_number,
                    "etag": part.etag,
                    "size_bytes": part.size_bytes,
                    "md5_checksum": part.md5_checksum,
                    "uploaded_at": part.uploaded_at.isoformat(),
                }
                for part in entity.completed_parts.values()
            ]

        return UploadSessionModel(
            upload_id=entity.upload_id,
            dataset_id=entity.dataset_id,
            bucket=entity.bucket,
            s3_key=entity.key,
            filename=entity.filename,
            content_type=entity.content_type,
            total_size=entity.total_size,
            part_size=entity.part_size,
            status=self._domain_status_to_model(entity.status),
            owner_id=entity.owner_id,
            completed_parts=completed_parts_json,
            uploaded_bytes=entity.uploaded_bytes,
            completed_part_count=len(entity.completed_parts),
        )

    def _update_model(self, model: UploadSessionModel, entity: UploadSession) -> None:
        """更新 ORM 模型字段。"""
        # 序列化已完成分片
        completed_parts_json = None
        if entity.completed_parts:
            completed_parts_json = [
                {
                    "part_number": part.part_number,
                    "etag": part.etag,
                    "size_bytes": part.size_bytes,
                    "md5_checksum": part.md5_checksum,
                    "uploaded_at": part.uploaded_at.isoformat(),
                }
                for part in entity.completed_parts.values()
            ]

        model.status = self._domain_status_to_model(entity.status)
        model.completed_parts = completed_parts_json
        model.uploaded_bytes = entity.uploaded_bytes
        model.completed_part_count = len(entity.completed_parts)

    # ========== IUploadSessionRepository 接口方法 ==========

    async def add(self, session: UploadSession) -> UploadSession:
        """添加新上传会话（委托给 EnhancedBaseRepository.create）。"""
        return await self.create(session)

    # ========== 领域特定查询方法 ==========

    async def get_by_upload_id(self, upload_id: str) -> UploadSession | None:
        """根据 S3 upload_id 获取上传会话。"""
        result = await self._session.execute(
            select(UploadSessionModel).where(UploadSessionModel.upload_id == upload_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_active_by_dataset(self, dataset_id: int) -> UploadSession | None:
        """获取数据集的活跃上传会话。"""
        result = await self._session.execute(
            select(UploadSessionModel).where(
                UploadSessionModel.dataset_id == dataset_id,
                or_(
                    UploadSessionModel.status == UploadSessionStatus.INITIATED,
                    UploadSessionModel.status == UploadSessionStatus.IN_PROGRESS,
                ),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_owner(
        self,
        owner_id: int,
        status: UploadStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[UploadSession], int]:
        """列出用户的上传会话。"""
        query = select(UploadSessionModel).where(UploadSessionModel.owner_id == owner_id)
        count_query = select(func.count(UploadSessionModel.id)).where(UploadSessionModel.owner_id == owner_id)

        # 应用状态过滤
        if status is not None:
            model_status = self._domain_status_to_model(status)
            query = query.where(UploadSessionModel.status == model_status)
            count_query = count_query.where(UploadSessionModel.status == model_status)

        # 获取总数
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # 应用排序（按创建时间降序）
        query = query.order_by(UploadSessionModel.created_at.desc())

        # 应用分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # 执行查询
        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._to_entity(m) for m in models], total

    async def list_expired(
        self,
        before: datetime,
        limit: int = 100,
    ) -> list[UploadSession]:
        """列出过期的上传会话。"""
        result = await self._session.execute(
            select(UploadSessionModel)
            .where(
                or_(
                    # 已完成/取消/失败且过期
                    UploadSessionModel.status.in_(
                        [
                            UploadSessionStatus.COMPLETED,
                            UploadSessionStatus.ABORTED,
                            UploadSessionStatus.FAILED,
                        ]
                    ),
                    # 或者超过过期时间
                    UploadSessionModel.expires_at < before,
                )
            )
            .order_by(UploadSessionModel.created_at.asc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
