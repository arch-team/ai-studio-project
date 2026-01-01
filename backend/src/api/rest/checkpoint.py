"""Checkpoint管理REST API

提供checkpoint的注册、查询、删除和迁移功能
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.checkpoint import (
    CheckpointCreate,
    CheckpointDeleteResponse,
    CheckpointListResponse,
    CheckpointMigrateRequest,
    CheckpointMigrateResponse,
    CheckpointResponse,
)
from config.database import get_db
from models.training import CheckpointStorageType
from services.checkpoint import CheckpointService, S3MigrationService
from services.checkpoint.storage_migration_service import StorageMigrationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/checkpoints", tags=["Checkpoints"])


@router.post("/", response_model=CheckpointResponse, status_code=status.HTTP_201_CREATED)
async def register_checkpoint(
    data: CheckpointCreate,
    session: AsyncSession = Depends(get_db),
):
    """注册新的checkpoint

    训练脚本保存checkpoint后调用此接口记录到数据库

    Args:
        data: Checkpoint创建数据
        session: 数据库会话

    Returns:
        创建的Checkpoint对象

    Raises:
        HTTPException 400: 训练任务不存在
        HTTPException 500: 服务器内部错误
    """
    service = CheckpointService(session)
    try:
        checkpoint = await service.register_checkpoint(
            job_id=data.job_id,
            step=data.step,
            storage_path=data.storage_path,
            storage_type=data.storage_type,
            size_bytes=data.size_bytes,
            epoch=data.epoch,
            metadata=data.metadata,
            metrics=data.metrics,
        )
        return checkpoint
    except ValueError as e:
        logger.error(f"注册checkpoint失败: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"注册checkpoint异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册checkpoint失败: {str(e)}",
        )


@router.get("/jobs/{job_id}", response_model=CheckpointListResponse)
async def list_checkpoints(
    job_id: int,
    storage_type: Optional[CheckpointStorageType] = Query(
        None, description="存储类型过滤"
    ),
    limit: int = Query(100, description="最大返回数量", ge=1, le=1000),
    offset: int = Query(0, description="偏移量", ge=0),
    session: AsyncSession = Depends(get_db),
):
    """列举训练任务的所有checkpoint

    Args:
        job_id: 训练任务ID
        storage_type: 存储类型过滤(可选)
        limit: 最大返回数量
        offset: 偏移量
        session: 数据库会话

    Returns:
        Checkpoint列表和总数
    """
    service = CheckpointService(session)
    checkpoints = await service.list_checkpoints(
        job_id=job_id,
        storage_type=storage_type,
        limit=limit,
        offset=offset,
    )
    return {"checkpoints": checkpoints, "total": len(checkpoints)}


@router.get("/jobs/{job_id}/latest", response_model=CheckpointResponse)
async def get_latest_checkpoint(
    job_id: int,
    storage_type: Optional[CheckpointStorageType] = Query(
        None, description="存储类型过滤"
    ),
    session: AsyncSession = Depends(get_db),
):
    """获取最新checkpoint(用于恢复训练)

    优先查找LOCAL/FSX,最后查S3(按性能排序)

    Args:
        job_id: 训练任务ID
        storage_type: 存储类型过滤(可选)
        session: 数据库会话

    Returns:
        最新Checkpoint对象

    Raises:
        HTTPException 404: 未找到checkpoint
    """
    service = CheckpointService(session)
    checkpoint = await service.get_latest_checkpoint(
        job_id=job_id, storage_type=storage_type
    )
    if not checkpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到训练任务的checkpoint: job_id={job_id}",
        )
    return checkpoint


@router.get("/{checkpoint_id}", response_model=CheckpointResponse)
async def get_checkpoint(
    checkpoint_id: int,
    session: AsyncSession = Depends(get_db),
):
    """根据ID获取checkpoint详情

    Args:
        checkpoint_id: Checkpoint ID
        session: 数据库会话

    Returns:
        Checkpoint对象

    Raises:
        HTTPException 404: Checkpoint不存在
    """
    service = CheckpointService(session)
    checkpoint = await service.get_checkpoint_by_id(checkpoint_id)
    if not checkpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint不存在: id={checkpoint_id}",
        )
    return checkpoint


@router.delete("/{checkpoint_id}", response_model=CheckpointDeleteResponse)
async def delete_checkpoint(
    checkpoint_id: int,
    session: AsyncSession = Depends(get_db),
):
    """删除单个checkpoint

    Args:
        checkpoint_id: Checkpoint ID
        session: 数据库会话

    Returns:
        删除结果

    Raises:
        HTTPException 404: Checkpoint不存在
    """
    service = CheckpointService(session)
    success = await service.delete_checkpoint(checkpoint_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint不存在: id={checkpoint_id}",
        )
    return {
        "success": True,
        "message": f"Checkpoint删除成功: id={checkpoint_id}",
    }


@router.delete(
    "/jobs/{job_id}/cleanup", response_model=CheckpointDeleteResponse
)
async def cleanup_old_checkpoints(
    job_id: int,
    keep_last_n: int = Query(5, description="保留最近N个checkpoint", ge=1, le=100),
    storage_type: Optional[CheckpointStorageType] = Query(
        None, description="存储类型过滤"
    ),
    session: AsyncSession = Depends(get_db),
):
    """清理旧checkpoint(保留最近N个)

    Args:
        job_id: 训练任务ID
        keep_last_n: 保留最近N个checkpoint
        storage_type: 存储类型过滤(可选)
        session: 数据库会话

    Returns:
        删除结果和删除数量
    """
    service = CheckpointService(session)
    deleted_count = await service.delete_old_checkpoints(
        job_id=job_id,
        keep_last_n=keep_last_n,
        storage_type=storage_type,
    )
    return {
        "success": True,
        "message": f"清理旧checkpoint完成: deleted={deleted_count}, kept={keep_last_n}",
        "deleted_count": deleted_count,
    }


@router.post("/migrate", response_model=CheckpointMigrateResponse)
async def migrate_checkpoint_to_s3(
    data: CheckpointMigrateRequest,
    session: AsyncSession = Depends(get_db),
):
    """迁移checkpoint到S3长期存储

    Args:
        data: 迁移请求数据
        session: 数据库会话

    Returns:
        迁移结果和S3 URI

    Raises:
        HTTPException 404: Checkpoint不存在
        HTTPException 400: Checkpoint已在S3或源文件不存在
        HTTPException 500: S3上传失败
    """
    # 获取checkpoint记录
    checkpoint_service = CheckpointService(session)
    checkpoint = await checkpoint_service.get_checkpoint_by_id(data.checkpoint_id)
    if not checkpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint不存在: id={data.checkpoint_id}",
        )

    # 执行S3迁移
    s3_service = S3MigrationService()
    try:
        s3_uri = await s3_service.migrate_to_s3(
            checkpoint=checkpoint,
            delete_source=data.delete_source,
        )

        # 更新数据库记录
        checkpoint.storage_path = s3_uri
        checkpoint.storage_type = CheckpointStorageType.S3
        await session.commit()

        return {
            "success": True,
            "s3_uri": s3_uri,
            "message": f"Checkpoint迁移到S3成功: id={data.checkpoint_id}",
        }

    except ValueError as e:
        logger.error(f"迁移checkpoint失败: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileNotFoundError as e:
        logger.error(f"迁移checkpoint失败(源文件不存在): {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"迁移checkpoint异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"迁移checkpoint失败: {str(e)}",
        )


@router.post("/migrate/policy", tags=["admin"])
async def run_migration_policy(
    session: AsyncSession = Depends(get_db),
):
    """手动触发分层存储迁移策略(管理员)

    执行完整的分层存储迁移策略:
    - NVMe → FSx (7天后)
    - FSx → S3 (30天后)
    - 最后checkpoint立即迁移到S3

    Returns:
        迁移统计信息

    Raises:
        HTTPException 500: 迁移失败
    """
    service = StorageMigrationService(session)
    try:
        stats = await service.run_migration_policy()
        return {
            "success": True,
            "stats": stats,
            "message": "分层存储迁移策略执行完成",
        }
    except Exception as e:
        logger.error(f"执行迁移策略失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行迁移策略失败: {str(e)}",
        )


@router.post("/{checkpoint_id}/migrate/fsx", tags=["admin"])
async def migrate_to_fsx(
    checkpoint_id: int,
    delete_source: bool = Query(True, description="是否删除源文件"),
    session: AsyncSession = Depends(get_db),
):
    """手动迁移checkpoint到FSx(管理员)

    Args:
        checkpoint_id: Checkpoint ID
        delete_source: 是否删除NVMe源文件
        session: 数据库会话

    Returns:
        迁移结果

    Raises:
        HTTPException 404: Checkpoint不存在
        HTTPException 400: Checkpoint不在NVMe上
        HTTPException 500: 迁移失败
    """
    service = StorageMigrationService(session)

    # 查询checkpoint
    checkpoint_service = CheckpointService(session)
    ckpt = await checkpoint_service.get_checkpoint_by_id(checkpoint_id)
    if not ckpt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint不存在: id={checkpoint_id}",
        )

    # 执行迁移
    success = await service.migrate_nvme_to_fsx(ckpt, delete_source=delete_source)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="迁移到FSx失败",
        )

    return {
        "success": True,
        "checkpoint_id": checkpoint_id,
        "storage_path": ckpt.storage_path,
        "message": "Checkpoint迁移到FSx成功",
    }


@router.post("/{checkpoint_id}/migrate/s3-from-fsx", tags=["admin"])
async def migrate_to_s3_from_fsx(
    checkpoint_id: int,
    delete_source: bool = Query(True, description="是否删除源文件"),
    session: AsyncSession = Depends(get_db),
):
    """手动迁移checkpoint从FSx到S3(管理员)

    Args:
        checkpoint_id: Checkpoint ID
        delete_source: 是否删除FSx源文件
        session: 数据库会话

    Returns:
        迁移结果

    Raises:
        HTTPException 404: Checkpoint不存在
        HTTPException 400: Checkpoint不在FSx上
        HTTPException 500: 迁移失败
    """
    service = StorageMigrationService(session)

    # 查询checkpoint
    checkpoint_service = CheckpointService(session)
    ckpt = await checkpoint_service.get_checkpoint_by_id(checkpoint_id)
    if not ckpt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint不存在: id={checkpoint_id}",
        )

    # 执行迁移
    success = await service.migrate_fsx_to_s3(ckpt, delete_source=delete_source)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="迁移到S3失败",
        )

    return {
        "success": True,
        "checkpoint_id": checkpoint_id,
        "storage_path": ckpt.storage_path,
        "message": "Checkpoint从FSx迁移到S3成功",
    }


__all__ = ["router"]
