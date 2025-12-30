"""训练任务REST API

提供训练任务的CRUD操作和状态管理
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas.training import (
    TrainingJobCreate,
    TrainingJobListResponse,
    TrainingJobResponse,
    TrainingJobStatusResponse,
    TrainingJobUpdate,
)
from core.database import get_db
from models.training import TrainingJob
from models.user import User
from services.training.job_service import TrainingJobService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])


# ==================== 依赖项 ====================


def get_training_job_service() -> TrainingJobService:
    """获取训练任务服务实例"""
    return TrainingJobService()


async def get_current_user() -> User:
    """获取当前用户(临时实现,待RBAC系统完成后替换)"""
    # TODO: 从认证令牌获取当前用户
    return User(id=1, username="admin", email="admin@example.com")


# ==================== API端点 ====================


@router.post(
    "/jobs",
    response_model=TrainingJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建训练任务",
    description="创建新的训练任务,包含完整配置信息",
)
async def create_training_job(
    job_data: TrainingJobCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """创建训练任务"""
    try:
        # 转换配置为字典
        config_dict = job_data.config.model_dump()

        # 创建训练任务
        job = await service.create_training_job(
            db=db,
            project_id=job_data.project_id,
            creator_id=current_user.id,
            name=job_data.name,
            job_type=job_data.job_type,
            framework=job_data.framework,
            config=config_dict,
            description=job_data.description,
        )

        # 重新查询以加载关联数据
        result = await db.execute(
            select(TrainingJob)
            .where(TrainingJob.id == job.id)
            .options(selectinload(TrainingJob.config))
        )
        job = result.scalar_one()

        return TrainingJobResponse.model_validate(job)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"创建训练任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建训练任务失败",
        ) from e


@router.get(
    "/jobs",
    response_model=TrainingJobListResponse,
    summary="查询训练任务列表",
    description="分页查询训练任务列表,支持按项目、状态过滤",
)
async def list_training_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    project_id: int | None = Query(default=None, description="项目ID过滤"),
    status_filter: str | None = Query(default=None, description="状态过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
) -> TrainingJobListResponse:
    """查询训练任务列表"""
    try:
        # 构建基础查询
        query = select(TrainingJob).where(TrainingJob.deleted_at.is_(None))

        # 项目过滤
        if project_id is not None:
            query = query.where(TrainingJob.project_id == project_id)

        # 状态过滤
        if status_filter:
            query = query.where(TrainingJob.status == status_filter)

        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # 分页查询
        query = (
            query.options(selectinload(TrainingJob.config))
            .order_by(TrainingJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(query)
        jobs = result.scalars().all()

        return TrainingJobListResponse(
            total=total,
            items=[TrainingJobResponse.model_validate(job) for job in jobs],
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"查询训练任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询训练任务列表失败",
        ) from e


@router.get(
    "/jobs/{job_id}",
    response_model=TrainingJobResponse,
    summary="查询训练任务详情",
    description="根据ID查询训练任务的详细信息",
)
async def get_training_job(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """查询训练任务详情"""
    try:
        result = await db.execute(
            select(TrainingJob)
            .where(TrainingJob.id == job_id, TrainingJob.deleted_at.is_(None))
            .options(selectinload(TrainingJob.config))
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在"
            )

        return TrainingJobResponse.model_validate(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询训练任务详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询训练任务详情失败",
        ) from e


@router.patch(
    "/jobs/{job_id}",
    response_model=TrainingJobResponse,
    summary="更新训练任务",
    description="更新训练任务的基本信息(名称、描述)",
)
async def update_training_job(
    job_id: int,
    job_data: TrainingJobUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """更新训练任务"""
    try:
        result = await db.execute(
            select(TrainingJob)
            .where(TrainingJob.id == job_id, TrainingJob.deleted_at.is_(None))
            .options(selectinload(TrainingJob.config))
        )
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在"
            )

        # 更新字段
        if job_data.name is not None:
            job.name = job_data.name
        if job_data.description is not None:
            job.description = job_data.description

        await db.commit()
        await db.refresh(job)

        return TrainingJobResponse.model_validate(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新训练任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新训练任务失败",
        ) from e


@router.post(
    "/jobs/{job_id}/start",
    response_model=TrainingJobResponse,
    summary="启动训练任务",
    description="启动处于PENDING状态的训练任务",
)
async def start_training_job(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """启动训练任务"""
    try:
        job = await service.start_training_job(db=db, job_id=job_id)

        # 重新查询以加载关联数据
        result = await db.execute(
            select(TrainingJob)
            .where(TrainingJob.id == job.id)
            .options(selectinload(TrainingJob.config))
        )
        job = result.scalar_one()

        return TrainingJobResponse.model_validate(job)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"启动训练任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="启动训练任务失败",
        ) from e


@router.post(
    "/jobs/{job_id}/stop",
    response_model=TrainingJobResponse,
    summary="停止训练任务",
    description="停止正在运行的训练任务",
)
async def stop_training_job(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """停止训练任务"""
    try:
        job = await service.stop_training_job(db=db, job_id=job_id)

        # 重新查询以加载关联数据
        result = await db.execute(
            select(TrainingJob)
            .where(TrainingJob.id == job.id)
            .options(selectinload(TrainingJob.config))
        )
        job = result.scalar_one()

        return TrainingJobResponse.model_validate(job)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"停止训练任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停止训练任务失败",
        ) from e


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除训练任务",
    description="删除训练任务(软删除)",
)
async def delete_training_job(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    force: bool = Query(default=False, description="强制删除活跃任务"),
) -> None:
    """删除训练任务"""
    try:
        success = await service.delete_training_job(db=db, job_id=job_id, force=force)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在"
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除训练任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除训练任务失败",
        ) from e


@router.get(
    "/jobs/{job_id}/status",
    response_model=TrainingJobStatusResponse,
    summary="查询训练任务状态",
    description="查询训练任务的实时状态(含K8S信息)",
)
async def get_training_job_status(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobStatusResponse:
    """查询训练任务状态"""
    try:
        status_info = await service.get_training_job_status(db=db, job_id=job_id)
        return TrainingJobStatusResponse(**status_info)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"查询训练任务状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询训练任务状态失败",
        ) from e


@router.post(
    "/jobs/{job_id}/sync",
    response_model=TrainingJobResponse,
    summary="同步训练任务状态",
    description="从K8S集群同步训练任务状态",
)
async def sync_training_job_status(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """同步训练任务状态"""
    try:
        job = await service.sync_job_status(db=db, job_id=job_id)

        # 重新查询以加载关联数据
        result = await db.execute(
            select(TrainingJob)
            .where(TrainingJob.id == job.id)
            .options(selectinload(TrainingJob.config))
        )
        job = result.scalar_one()

        return TrainingJobResponse.model_validate(job)

    except Exception as e:
        logger.error(f"同步训练任务状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="同步训练任务状态失败",
        ) from e


__all__ = ["router"]
