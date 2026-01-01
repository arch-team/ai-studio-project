"""训练任务REST API

提供训练任务的CRUD操作和状态管理
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas.training import (
    CheckpointResponse,
    TrainingJobCreate,
    TrainingJobListResponse,
    TrainingMetricsResponse,
    TrainingJobResponse,
    TrainingJobStatusResponse,
    TrainingJobUpdate,
)
from config.database import get_db
from models.training import Checkpoint, TrainingJob, TrainingJobMetrics
from models.user import User
from services.checkpoint.checkpoint_service import CheckpointService
from services.training.job_service import TrainingJobService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["training"])


# ==================== 依赖项 ====================


async def get_training_job_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TrainingJobService:
    """获取训练任务服务实例"""
    return TrainingJobService(session=db)


async def get_checkpoint_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> CheckpointService:
    """获取检查点服务实例"""
    return CheckpointService(session=db)


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
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """创建训练任务"""
    try:
        # 创建训练任务
        job = await service.create_training_job(
            job_data=job_data,
            creator=current_user,
        )

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
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    project_id: int | None = Query(default=None, description="项目ID过滤"),
    status_filter: str | None = Query(default=None, description="状态过滤"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
) -> TrainingJobListResponse:
    """查询训练任务列表"""
    try:
        # 使用service层查询
        jobs, total = await service.list_training_jobs(
            project_id=project_id,
            status=status_filter,
            page=page,
            size=page_size,
        )

        # 计算总页数
        pages = (total + page_size - 1) // page_size

        return TrainingJobListResponse(
            total=total,
            items=[TrainingJobResponse.model_validate(job) for job in jobs],
            page=page,
            size=page_size,
            pages=pages,
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
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """查询训练任务详情"""
    try:
        # 使用service层查询(包含配置信息)
        job = await service.get_training_job(job_id, include_config=True)

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
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """更新训练任务"""
    try:
        # 使用service层更新
        job = await service.update_training_job(job_id, job_data)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在"
            )

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
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TrainingJobResponse:
    """启动训练任务"""
    try:
        # 使用service层启动
        job = await service.start_training_job(job_id)

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
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    save_checkpoint: bool = Query(default=True, description="是否保存检查点"),
) -> TrainingJobResponse:
    """停止训练任务"""
    try:
        # 使用service层停止
        job = await service.stop_training_job(job_id, save_checkpoint=save_checkpoint)

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
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """删除训练任务"""
    try:
        # 使用service层删除
        success = await service.delete_training_job(job_id)

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


@router.get(
    "/jobs/{job_id}/metrics",
    response_model=list[TrainingMetricsResponse],
    summary="查询训练任务指标",
    description="查询训练任务的历史指标数据",
)
async def get_training_job_metrics(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
) -> list[TrainingMetricsResponse]:
    """查询训练任务指标"""
    try:
        # 验证任务存在
        result = await db.execute(
            select(TrainingJob).where(
                TrainingJob.id == job_id, TrainingJob.deleted_at.is_(None)
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在"
            )

        # 查询指标数据
        result = await db.execute(
            select(TrainingJobMetrics)
            .where(TrainingJobMetrics.job_id == job_id)
            .order_by(TrainingJobMetrics.step.desc())
            .limit(limit)
            .offset(offset)
        )
        metrics = result.scalars().all()

        return [TrainingMetricsResponse.model_validate(m) for m in metrics]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询训练任务指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询训练任务指标失败",
        ) from e


@router.get(
    "/jobs/{job_id}/logs",
    response_model=dict[str, Any],
    summary="查询训练任务日志",
    description="查询训练任务的Pod日志",
)
async def get_training_job_logs(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[TrainingJobService, Depends(get_training_job_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    tail_lines: int = Query(default=100, ge=1, le=10000, description="尾部行数"),
    pod_name: str | None = Query(default=None, description="指定Pod名称"),
) -> dict[str, Any]:
    """查询训练任务日志"""
    try:
        # 验证任务存在
        result = await db.execute(
            select(TrainingJob).where(
                TrainingJob.id == job_id, TrainingJob.deleted_at.is_(None)
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在"
            )

        # 获取日志
        logs = await service.get_job_logs(
            job_id=job_id, tail_lines=tail_lines, pod_name=pod_name
        )

        return {
            "job_id": job_id,
            "pod_name": pod_name,
            "tail_lines": tail_lines,
            "logs": logs,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询训练任务日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询训练任务日志失败",
        ) from e


@router.get(
    "/jobs/{job_id}/checkpoints",
    response_model=list[CheckpointResponse],
    summary="查询训练任务检查点",
    description="查询训练任务的检查点列表",
)
async def get_training_job_checkpoints(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    checkpoint_service: Annotated[CheckpointService, Depends(get_checkpoint_service)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=10, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
) -> list[CheckpointResponse]:
    """查询训练任务检查点"""
    try:
        # 验证任务存在
        result = await db.execute(
            select(TrainingJob).where(
                TrainingJob.id == job_id, TrainingJob.deleted_at.is_(None)
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="训练任务不存在"
            )

        # 查询检查点
        checkpoints = await checkpoint_service.list_checkpoints(
            db=db, job_id=job_id, limit=limit, offset=offset
        )

        return [CheckpointResponse.model_validate(cp) for cp in checkpoints]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询训练任务检查点失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询训练任务检查点失败",
        ) from e


__all__ = ["router"]
